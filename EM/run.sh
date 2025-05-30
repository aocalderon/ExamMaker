#!/bin/bash

# Check if argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <max_value>"
  exit 1
fi

# Loop from 1 to the value of the first argument
for ((i = 1; i <= $1; i++))
do
  echo "Exam $i..."
  python3 ExamMaker.py
done

rm exams/*.log
rm exams/*.aux
