import re

from six import string_types

class Action(object):
    """
    Base class for intrinsic function actions. Each intrinsic function must subclass this,
    override the intrinsic_name, and provide a resolve() method

    Subclasses would be working on the JSON representation of an intrinsic function like {Ref: foo} than the YAML
    version !Ref foo because the input is already in JSON.
    """

    _resource_ref_separator = "."
    intrinsic_name = None

    def __init__(self):
        if not self.intrinsic_name:
            raise TypeError("Subclass must provide a intrinsic_name")

    def resolve_parameter_refs(self, input_dict, parameters):
        """
        Subclass must implement this method to resolve the intrinsic function
        """
        raise NotImplementedError("Subclass must implement this method")

    def resolve_resource_refs(self, input_dict, supported_resource_refs):
        """
        Subclass must implement this method to resolve resource references
        """
        raise NotImplementedError("Subclass must implement this method")

    def can_handle(self, input_dict):
        """
        Validates that the input dictionary contains only one key and is of the given intrinsic_name

        :param input_dict: Input dictionary representing the intrinsic function
        :return: True if it matches expected structure, False otherwise
        """

        return input_dict is not None \
                   and isinstance(input_dict, dict) \
                   and len(input_dict) == 1 \
                   and self.intrinsic_name in input_dict

    @classmethod
    def _parse_resource_reference(cls, ref_value):
        """
        Splits a resource reference of structure "LogicalId.Property" and returns the "LogicalId" and "Property" separately.

        :param string ref_value: Input reference value which *may* contain the structure "LogicalId.Property"
        :return string, string: Returns two values - logical_id, property. If the input does not contain the structure,
            then both `logical_id` and property will be None

        """
        no_result = (None, None)

        if not isinstance(ref_value, string_types):
            return no_result

        splits = ref_value.split(cls._resource_ref_separator, 1)

        # Either there is no 'dot' (or) one of the values is empty string (Ex: when you split "LogicalId.")
        if len(splits) != 2 or not all(splits):
            return no_result

        return splits[0], splits[1]


class RefAction(Action):
    intrinsic_name = "Ref"

    def resolve_parameter_refs(self, input_dict, parameters):
        """
        Resolves references that are present in the parameters and returns the value. If it is not in parameters,
        this method simply returns the input unchanged.

        :param input_dict: Dictionary representing the Ref function. Must contain only one key and it should be "Ref".
            Ex: {Ref: "foo"}

        :param parameters: Dictionary of parameter values for resolution
        :return:
        """
        if not self.can_handle(input_dict):
            return input_dict

        param_name = input_dict[self.intrinsic_name]

        if not isinstance(param_name, string_types):
            return input_dict

        if param_name in parameters:
            return parameters[param_name]
        else:
            return input_dict

    def resolve_resource_refs(self, input_dict, supported_resource_refs):
        """
        Resolves references to some property of a resource. These are runtime properties which can't be converted
        to a value here. Instead we output another reference that will more actually resolve to the value when
        executed via CloudFormation

        Example:
            {"Ref": "LogicalId.Property"} => {"Ref": "SomeOtherLogicalId"}

        :param dict input_dict: Dictionary representing the Ref function to be resolved.
        :param samtranslator.intrinsics.resource_refs.SupportedResourceReferences supported_resource_refs: Instance of
            an `SupportedResourceReferences` object that contain value of the property.
        :return dict: Dictionary with resource references resolved.
        """

        if not self.can_handle(input_dict):
            return input_dict

        ref_value = input_dict[self.intrinsic_name]
        logical_id, property = self._parse_resource_reference(ref_value)

        # ref_value could not be parsed
        if not logical_id:
            return input_dict

        resolved_value = supported_resource_refs.get(logical_id, property)
        if not resolved_value:
            return input_dict

        return {
            self.intrinsic_name: resolved_value
        }

class SubAction(Action):
    intrinsic_name = "Fn::Sub"

    def resolve_parameter_refs(self, input_dict, parameters):
        """
        Substitute references found within the string of `Fn::Sub` intrinsic function

        :param input_dict: Dictionary representing the Fn::Sub function. Must contain only one key and it should be
            `Fn::Sub`. Ex: {"Fn::Sub": ...}

        :param parameters: Dictionary of parameter values for substitution
        :return: Resolved
        """
        if not self.can_handle(input_dict):
            return input_dict

        key = self.intrinsic_name
        value = input_dict[key]

        def do_replacement(full_ref, prop_name):
            """
            Replace parameter references with actual value. Return value of this method is directly replaces the
            reference structure

            :param full_ref: => ${logicalId.property}
            :param prop_name: => logicalId.property
            :return: Either the value it resolves to. If not the original reference
            """
            return parameters.get(prop_name, full_ref)

        input_dict[key] = self._handle_sub_value(value, do_replacement)

        return input_dict

    def resolve_resource_refs(self, input_dict, supported_resource_refs):
        """
        Resolves reference to some property of a resource. Inside string to be substituted, there could be either a
        "Ref" or a "GetAtt" usage of this property. They have to be handled differently.

        Ref usages are directly converted to a Ref on the resolved value. GetAtt usages are split under the assumption
        that there can be only one property of resource referenced here. Everything else is an attribute reference.

        Example:

            Let's say `LogicalId.Property` will be resolved to `ResolvedValue`

            Ref usage:
                ${LogicalId.Property}  => ${ResolvedValue}

            GetAtt usage:
                ${LogicalId.Property.Arn} => ${ResolvedValue.Arn}
                ${LogicalId.Property.Attr1.Attr2} => {ResolvedValue.Attr1.Attr2}


        :param input_dict: Dictionary to be resolved
        :param samtranslator.intrinsics.resource_refs.SupportedResourceReferences supported_resource_refs: Instance of
            an `SupportedResourceReferences` object that contain value of the property.
        :return: Resolved dictionary
        """

        if not self.can_handle(input_dict):
            return input_dict

        key = self.intrinsic_name
        sub_value = input_dict[key]

        def do_replacement(full_ref, ref_value):
            """
            Perform the appropriate replacement to handle ${LogicalId.Property} type references inside a Sub.
            This method is called to get the replacement string for each reference within Sub's value

            :param full_ref: Entire reference string such as "${LogicalId.Property}"
            :param ref_value: Just the value of the reference such as "LogicalId.Property"
            :return: Resolved reference of the structure "${SomeOtherLogicalId}". Result should always include the
                ${} structure since we are not resolving to final value, but just converting one reference to another
            """

            # Split the value by separator, expecting to separate out LogicalId.Property
            splits = ref_value.split(self._resource_ref_separator)

            # If we don't find at least two parts, there is nothing to resolve
            if len(splits) < 2:
                return full_ref

            logical_id = splits[0]
            property = splits[1]
            resolved_value = supported_resource_refs.get(logical_id, property)
            if not resolved_value:
                # This ID/property combination is not in the supported references
                return full_ref

            # We found a LogicalId.Property combination that can be resolved. Construct the output by replacing
            # the part of the reference string and not constructing a new ref. This allows us to support GetAtt-like
            # syntax and retain other attributes. Ex: ${LogicalId.Property.Arn} => ${SomeOtherLogicalId.Arn}
            replacement = self._resource_ref_separator.join([logical_id, property])
            return full_ref.replace(replacement, resolved_value)

        input_dict[key] = self._handle_sub_value(sub_value, do_replacement)

        return input_dict


    def _handle_sub_value(self, sub_value, handler_method):
        """
        Generic method to handle value to Fn::Sub key. We are interested in parsing the ${} syntaxes inside
        the string portion of the value.

        :param sub_value: Value of the Sub function
        :param handler_method: Method to be called on every occurrence of `${LogicalId}` structure within the string.
            Implementation could resolve and replace this structure with whatever they seem fit
        :return: Resolved value of the Sub dictionary
        """

        # Just handle known references within the string to be substituted and return the whole dictionary
        # because that's the best we can do here.
        if isinstance(sub_value, string_types):
            # Ex: {Fn::Sub: "some string"}
            sub_value = self._sub_all_refs(sub_value, handler_method)

        elif isinstance(sub_value, list) and len(sub_value) > 0 and isinstance(sub_value[0], string_types):
            # Ex: {Fn::Sub: ["some string", {a:b}] }
            sub_value[0] = self._sub_all_refs(sub_value[0], handler_method)

        return sub_value

    def _sub_all_refs(self, text, handler_method):
        """
        Substitute references within a string that is using ${key} syntax by calling the `handler_method` on every
        occurrence of this structure. The value returned by this method directly replaces the reference structure.

        Ex:
            text = "${key1}-hello-${key2}
            def handler_method(full_ref, ref_value):
                return "foo"

            _sub_all_refs(text, handler_method) will output "foo-hello-foo"

        :param string text: Input text
        :param handler_method: Method to be called to handle each occurrence of ${blah} reference structure.
            First parameter to this method is the full reference structure Ex: ${LogicalId.Property}. Second parameter is just the
            value of the reference such as "LogicalId.Property"

        :return string: Text with all reference structures replaced as necessary
        """

        # RegExp to find pattern "${logicalId.property}" and return the word inside bracket
        logical_id_regex = '[A-Za-z0-9\.]+'
        ref_pattern = re.compile(r'\$\{('+logical_id_regex+')\}')

        # Find all the pattern, and call the handler to decide how to substitute them.
        # Do the substitution and return the final text
        return re.sub(ref_pattern,
                      # Pass the handler entire string ${logicalId.property} as first parameter and "logicalId.property"
                      # as second parameter. Return value will be substituted
                      lambda match: handler_method(match.group(0), match.group(1)),
                      text)

class GetAttAction(Action):
    intrinsic_name = "Fn::GetAtt"

    def resolve_parameter_refs(self, input_dict, parameters):
        # Parameters can never be referenced within GetAtt value
        return input_dict


    def resolve_resource_refs(self, input_dict, supported_resource_refs):
        """
        Resolve resource references within a GetAtt dict.

        Example:
            { "Fn::GetAtt": ["LogicalId.Property", "Arn"] }  =>  {"Fn::GetAtt":  ["ResolvedLogicalId", "Arn"]}


        Theoretically, only the first element of the array can contain reference to SAM resources. The second element
        is name of an attribute (like Arn) of the resource.

        However tools like AWS CLI apply the assumption that first element of the array is a LogicalId and cannot
        contain a 'dot'. So they break at the first dot to convert YAML tag to JSON map like this:

             `!GetAtt LogicalId.Property.Arn` => {"Fn::GetAtt": [ "LogicalId", "Property.Arn" ] }

        Therefore to resolve the reference, we join the array into a string, break it back up to check if it contains
        a known reference, and resolve it if we can.

        :param input_dict: Dictionary to be resolved
        :param samtransaltor.intrinsics.resource_refs.SupportedResourceReferences supported_resource_refs: Instance of
            an `SupportedResourceReferences` object that contain value of the property.
        :return: Resolved dictionary
        """

        if not self.can_handle(input_dict):
            return input_dict

        key = self.intrinsic_name
        value = input_dict[key]

        # Value must be an array with *at least* two elements. If not, this is invalid GetAtt syntax. We just pass along
        # the input to CFN for it to do the "official" validation.
        if not isinstance(value, list) or len(value) < 2:
            return input_dict

        # Value of GetAtt is an array. It can contain any number of elements, with first being the LogicalId of
        # resource and rest being the attributes. In a SAM template, a reference to a resource can be used in the
        # first parameter. However tools like AWS CLI might break them down as well. So let's just concatenate
        # all elements, and break them into separate parts in a more standard way.
        #
        # Example:
        #   { Fn::GetAtt: ["LogicalId.Property", "Arn"] } is equivalent to { Fn::GetAtt: ["LogicalId", "Property.Arn"] }
        #   Former is the correct notation. However tools like AWS CLI can construct the later style.
        #   Let's normalize the value into "LogicalId.Property.Arn" to handle both scenarios

        value_str = self._resource_ref_separator.join(value)
        splits = value_str.split(self._resource_ref_separator)
        logical_id = splits[0]
        property = splits[1]
        remaining = splits[2:] # if any

        resolved_value = supported_resource_refs.get(logical_id, property)
        if resolved_value:
            # We resolved to a new resource logicalId. Use this as the first element and keep remaining elements intact
            # This is the new value of Fn::GetAtt
            input_dict[key] = [resolved_value] + remaining

        return input_dict
