# Generate slurm scripts

# reads in a slurm script and changes some parameters
# to run the same process on new data

with open('fic1950-54.slurm', 'r') as file:
    data = file.readlines()

decadefiles = dict()

for decade in range(1910, 1985, 5):
    decadefiles[decade] = []
    newspan = str(decade) + '-' + str(decade + 4)[-2:]
    if newspan == '1950-54':
        continue
    for line in data:
        if '1950-54' in line:
            newline = line.replace('1950-54', 'fic' + newspan)
            decadefiles[decade].append(newline)
        elif 'fiction/doctopics' in line:
            newline = line.replace('1950', str(decade))
            newline = newline.replace('1954', str(decade + 5))
            decadefiles[decade].append(newline)
        else:
            decadefiles[decade].append(line)

for key, value in decadefiles.items():
    with open('fic' + newspan + '.slurm', 'w') as file:
        file.writelines(value)
