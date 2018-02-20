'use strict';

const exec = require('child_process').exec;

exports.handler = (event, context, callback) => {
    if (!event.cmd) {
        return callback('Please specify a command to run as event.cmd');
    }
    const child = exec(event.cmd, (error) => {
        // Resolve with result of process
        callback(error, 'Process complete!');
    });

    // Log process stdout and stderr
    child.stdout.on('data', console.log);
    child.stderr.on('data', console.error);
};
