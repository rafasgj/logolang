#!/bin/sh

dir=$(dirname $0)
sources="${dir}/../examples"
expected="${dir}/../tests/expected"

exit_value=0

report() {
    echo -e "$*" >&2
}

for src in $(ls -1 "${sources}"/*.logo)
do
    filename=$(basename $src '.logo') 
    echo -en "Compiling \033[37;1m${filename}\033[0m... "
    if PYTHONPATH="${dir}/.." python ${dir}/../logolang/__main__.py ${src} > /tmp/a.out 2>/dev/null
    then
        echo -e "\033[32;1mDONE\033[0m"
        echo -n "Evaluating output... "
        if diff -Naur "${expected}/${filename}.lasm" /tmp/a.out 2>/dev/null >/dev/null
        then
            echo -e "\033[32;1mDONE\033[0m"
        else
            echo -e "\033[31;1mFAILED\033[0m"
            report "Found difference in expected output: '${filename}.logo'."
            exit_value=2
        fi
    else
        echo -e "\033[31;1mFAILED\033[0m"
        report "Failed to compile '${filename}.logo'"
        exit_value=1
    fi
done

[ ${exit_value} -eq 0 ] || exit ${exit_value}

echo "All tests passed."

