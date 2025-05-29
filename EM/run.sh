#!/bin/bash

for i in {1..20}
do
  echo "Exam $i..."
  /usr/bin/python3 /home/and/MEGA/Work/PUJ/2025-S1/DBS/Midterm3/ExamMaker.py
done

rm exams/*.log
rm exams/*.aux
