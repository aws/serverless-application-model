import re

from samtranslator.model.exceptions import InvalidTemplateException, InvalidDocumentException


class Action(object):
    """
    Base class for intrinsic function actions. Each intrinsic function must subclass this,
    override the intrinsic_name, and provide a resolve() method

    Subclasses would be working on the JSON representation of an intrinsic function like {Ref: foo} than the YAML
    version !Ref foo because the input is already in JSON.
    """

    _resource_ref_separator = "."

    # Note(xinhol): `Action` should have been an abstract class. Disabling the type check for the next
    # line to avoid any potential behavior change.
    # TODO: Make `Action` an abstract class and not giving `intrinsic_name` initial value.
    intrinsic_name: str = None  # type: ignore

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

    def resolve_resource_id_refs(self, input_dict, supported_resource_id_refs):
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

        return (
            input_dict is not None
            and isinstance(input_dict, dict)
            and len(input_dict) == 1
            and self.intrinsic_name in input_dict
        )

    @classmethod
    def _parse_resource_reference(cls, ref_value):
        """
        Splits a resource reference of structure "LogicalId.Property" and returns the "LogicalId" and "Property"
        separately.

        :param string ref_value: Input reference value which *may* contain the structure "LogicalId.Property"
        :return string, string: Returns two values - logical_id, property. If the input does not contain the structure,
            then both `logical_id` and property will be None

        """
        no_result = (None, None)

        if not isinstance(ref_value, str):
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

        if not isinstance(param_name, str):
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

        return {self.intrinsic_name: resolved_value}

    def resolve_resource_id_refs(self, input_dict, supported_resource_id_refs):
        """
        Updates references to the old logical id of a resource to the new (generated) logical id.

        Example:
            {"Ref": "MyLayer"} => {"Ref": "MyLayerABC123"}

        :param dict input_dict: Dictionary representing the Ref function to be resolved.
        :param dict supported_resource_id_refs: Dictionary that maps old logical ids to new ones.
        :return dict: Dictionary with resource references resolved.
        """

        if not self.can_handle(input_dict):
            return input_dict

        ref_value = input_dict[self.intrinsic_name]
        if not isinstance(ref_value, str) or self._resource_ref_separator in ref_value:
            return input_dict

        logical_id = ref_value

        resolved_value = supported_resource_id_refs.get(logical_id)
        if not resolved_value:
            return input_dict

        return {self.intrinsic_name: resolved_value}


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

        def do_replacement(full_ref, prop_name):
            """
            Replace parameter references with actual value. Return value of this method is directly replaces the
            reference structure

            :param full_ref: => ${logicalId.property}
            :param prop_name: => logicalId.property
            :return: Either the value it resolves to. If not the original reference
            """
            return parameters.get(prop_name, full_ref)

        return self._handle_sub_action(input_dict, do_replacement)

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

        return self._handle_sub_action(input_dict, do_replacement)

    def resolve_resource_id_refs(self, input_dict, supported_resource_id_refs):
        """
        Resolves reference to some property of a resource. Inside string to be substituted, there could be either a
        "Ref" or a "GetAtt" usage of this property. They have to be handled differently.

        Ref usages are directly converted to a Ref on the resolved value. GetAtt usages are split under the assumption
        that there can be only one property of resource referenced here. Everything else is an attribute reference.

        Example:

            Let's say `LogicalId` will be resolved to `NewLogicalId`

            Ref usage:
                ${LogicalId}  => ${NewLogicalId}

            GetAtt usage:
                ${LogicalId.Arn} => ${NewLogicalId.Arn}
                ${LogicalId.Attr1.Attr2} => {NewLogicalId.Attr1.Attr2}


        :param input_dict: Dictionary to be resolved
        :param dict supported_resource_id_refs: Dictionary that maps old logical ids to new ones.
        :return: Resolved dictionary
        """

        def do_replacement(full_ref, ref_value):
            """
            Perform the appropriate replacement to handle ${LogicalId} type references inside a Sub.
            This method is called to get the replacement string for each reference within Sub's value

            :param full_ref: Entire reference string such as "${LogicalId.Property}"
            :param ref_value: Just the value of the reference such as "LogicalId.Property"
            :return: Resolved reference of the structure "${SomeOtherLogicalId}". Result should always include the
                ${} structure since we are not resolving to final value, but just converting one reference to another
            """

            # Split the value by separator, expecting to separate out LogicalId
            splits = ref_value.split(self._resource_ref_separator)

            # If we don't find at least one part, there is nothing to resolve
            if len(splits) < 1:
                return full_ref

            logical_id = splits[0]
            resolved_value = supported_resource_id_refs.get(logical_id)
            if not resolved_value:
                # This ID/property combination is not in the supported references
                return full_ref

            # We found a LogicalId.Property combination that can be resolved. Construct the output by replacing
            # the part of the reference string and not constructing a new ref. This allows us to support GetAtt-like
            # syntax and retain other attributes. Ex: ${LogicalId.Property.Arn} => ${SomeOtherLogicalId.Arn}
            return full_ref.replace(logical_id, resolved_value)

        return self._handle_sub_action(input_dict, do_replacement)

    def _handle_sub_action(self, input_dict, handler):
        """
        Handles resolving replacements in the Sub action based on the handler that is passed as an input.

        :param input_dict: Dictionary to be resolved
        :param supported_values: One of several different objects that contain the supported values that
            need to be changed. See each method above for specifics on these objects.
        :param handler: handler that is specific to each implementation.
        :return: Resolved value of the Sub dictionary
        """
        if not self.can_handle(input_dict):
            return input_dict

        key = self.intrinsic_name
        sub_value = input_dict[key]

        input_dict[key] = self._handle_sub_value(sub_value, handler)

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
        if isinstance(sub_value, str):
            # Ex: {Fn::Sub: "some string"}
            sub_value = self._sub_all_refs(sub_value, handler_method)

        elif isinstance(sub_value, list) and len(sub_value) > 0 and isinstance(sub_value[0], str):
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
            First parameter to this method is the full reference structure Ex: ${LogicalId.Property}.
            Second parameter is just the value of the reference such as "LogicalId.Property"

        :return string: Text with all reference structures replaced as necessary
        """

        # RegExp to find pattern "${logicalId.property}" and return the word inside bracket
        logical_id_regex = r"[A-Za-z0-9\.]+|AWS::[A-Z][A-Za-z]*"
        ref_pattern = re.compile(r"\$\{(" + logical_id_regex + r")\}")

        # Find all the pattern, and call the handler to decide how to substitute them.
        # Do the substitution and return the final text
        # NOTE: in order to make sure Py27UniStr strings won't be converted to plain string,
        # we need to iterate through each match and do the replacement
        substituted = text
        for match in re.finditer(ref_pattern, text):
            sub_value = handler_method(match.group(0), match.group(1))
            substituted = substituted.replace(match.group(0), sub_value, 1)
        return substituted


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

        if not self._check_input_value(value):
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
        remaining = splits[2:]  # if any

        resolved_value = supported_resource_refs.get(logical_id, property)
        return self._get_resolved_dictionary(input_dict, key, resolved_value, remaining)

    def resolve_resource_id_refs(self, input_dict, supported_resource_id_refs):
        """
        Resolve resource references within a GetAtt dict.

        Example:
            { "Fn::GetAtt": ["LogicalId", "Arn"] }  =>  {"Fn::GetAtt":  ["ResolvedLogicalId", "Arn"]}


        Theoretically, only the first element of the array can contain reference to SAM resources. The second element
        is name of an attribute (like Arn) of the resource.

        However tools like AWS CLI apply the assumption that first element of the array is a LogicalId and cannot
        contain a 'dot'. So they break at the first dot to convert YAML tag to JSON map like this:

             `!GetAtt LogicalId.Arn` => {"Fn::GetAtt": [ "LogicalId", "Arn" ] }

        Therefore to resolve the reference, we join the array into a string, break it back up to check if it contains
        a known reference, and resolve it if we can.

        :param input_dict: Dictionary to be resolved
        :param dict supported_resource_id_refs: Dictionary that maps old logical ids to new ones.
        :return: Resolved dictionary
        """

        if not self.can_handle(input_dict):
            return input_dict

        key = self.intrinsic_name
        value = input_dict[key]

        if not self._check_input_value(value):
            return input_dict

        value_str = self._resource_ref_separator.join(value)
        splits = value_str.split(self._resource_ref_separator)
        logical_id = splits[0]
        remaining = splits[1:]  # if any

        resolved_value = supported_resource_id_refs.get(logical_id)
        return self._get_resolved_dictionary(input_dict, key, resolved_value, remaining)

    def _check_input_value(self, value):
        # Value must be an array with *at least* two elements. If not, this is invalid GetAtt syntax. We just pass along
        # the input to CFN for it to do the "official" validation.
        if not isinstance(value, list) or len(value) < 2:
            return False

        # If items in value array is not a string, then following join line will fail. So if any element is not a string
        # we just pass along the input to CFN for doing the validation
        for item in value:
            if not isinstance(item, str):
                return False

        return True

    def _get_resolved_dictionary(self, input_dict, key, resolved_value, remaining):
        """
        Resolves the function and returns the updated dictionary

        :param input_dict: Dictionary to be resolved
        :param key: Name of this intrinsic.
        :param resolved_value: Resolved or updated value for this action.
        :param remaining: Remaining sections for the GetAtt action.
        """
        if resolved_value:
            # We resolved to a new resource logicalId. Use this as the first element and keep remaining elements intact
            # This is the new value of Fn::GetAtt
            input_dict[key] = [resolved_value] + remaining

        return input_dict


class FindInMapAction(Action):
    """
    This action can't be used along with other actions.
    """

    intrinsic_name = "Fn::FindInMap"

    def resolve_parameter_refs(self, input_dict, parameters):
        """
        Recursively resolves "Fn::FindInMap"references that are present in the mappings and returns the value.
        If it is not in mappings, this method simply returns the input unchanged.

        :param input_dict: Dictionary representing the FindInMap function. Must contain only one key and it
                           should be "Fn::FindInMap".

        :param parameters: Dictionary of mappings from the SAM template
        """
        if not self.can_handle(input_dict):
            return input_dict

        value = input_dict[self.intrinsic_name]

        # FindInMap expects an array with 3 values
        if not isinstance(value, list) or len(value) != 3:
            raise InvalidDocumentException(
                [
                    InvalidTemplateException(
                        "Invalid FindInMap value {}. FindInMap expects an array with 3 values.".format(value)
                    )
                ]
            )

        map_name = self.resolve_parameter_refs(value[0], parameters)
        top_level_key = self.resolve_parameter_refs(value[1], parameters)
        second_level_key = self.resolve_parameter_refs(value[2], parameters)

        if not isinstance(map_name, str) or not isinstance(top_level_key, str) or not isinstance(second_level_key, str):
            return input_dict

        if (
            map_name not in parameters
            or top_level_key not in parameters[map_name]
            or second_level_key not in parameters[map_name][top_level_key]
        ):
            return input_dict

        return parameters[map_name][top_level_key][second_level_key]
