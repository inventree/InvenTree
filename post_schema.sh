#!/usr/bin/env bash

script_dir="$(realpath $(dirname "$0"))"
schema_file="$script_dir/${1:-schema.yml}"

# find fields that are conditionally removed
field_list=$(find $script_dir/src/backend/ -name \*serializers.py -exec sed -n "s/^.*pass # self.fields.pop('\([^']\+\)'.*$/\1/p" {} \; | sort -u)
# remove them from the lists of required fields
for field in $field_list; do
    sed -i "/- $field$/d" "$schema_file"
done

# restore original conditional removal of fields
find $script_dir/src/backend/ -name \*serializers.py -exec sed -i "s/pass # self.fields.pop/self.fields.pop/g" {} \;
