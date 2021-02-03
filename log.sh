# python3 main.py | tee log.txt

cat log.txt | fgrep octave | cut -d ' ' -f 4 | uniq
