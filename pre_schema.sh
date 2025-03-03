#!/usr/bin/env bash

script_dir="$(realpath $(dirname "$0"))"

# comment out conditional removal of fields as it causes the schema generator to exclude them unconditionally
find $script_dir/src/backend/ -name \*serializers.py -exec sed -i "s/self.fields.pop/pass # self.fields.pop/g" {} \;
