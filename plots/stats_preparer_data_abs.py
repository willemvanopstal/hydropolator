import os

keyword = 'abs'
depare_files = {}
separator = ';'

for file in os.listdir():
    if file.startswith(keyword):
        processName = file.split('_')[1]
        processName = processName.split('.')[0]
        depare_files[processName] = file

unorderedProcesses = list(depare_files.keys())
for i, item in enumerate(unorderedProcesses):
    print(' > ', item, '({})'.format(i))

print('now define order: ')
chosenOrder = input()
chosenOrder = [int(val) for val in chosenOrder.split(',')]

sortedProcesses = []
for entry in range(i+1):
    # print(entry)
    originalIndex = chosenOrder.index(entry)
    # print(chosenOrder.index(entry))
    # print(unorderedProcesses[originalIndex])
    sortedProcesses.append(unorderedProcesses[originalIndex])
print(sortedProcesses)

headerRow = 'process;interval;num_changes;intervalindex'
rowDict = {}

with open('stats_together_data_abs.csv', 'w') as outfile:
    outfile.write(headerRow + '\n')

    for process in sortedProcesses:
        print(process)
        totalArea = 0.0

        with open(depare_files[process]) as infile:
            ii = 0
            for line in infile.readlines():
                if not line.startswith('SEP'):
                    rowEntry = line.split(separator)
                    if rowEntry[0] == 'abs_change':
                        continue
                    # print(line.split(';'))
                    if rowEntry[0] == 'total':
                        totalArea = float(rowEntry[-1].strip().replace(',', '.'))
                        print(totalArea)
                    else:
                        depare_region = rowEntry[0]
                        rowValue = float(rowEntry[-1].strip().replace(',', '.'))
                        # rowPercentage = round(rowValue / totalArea, 4)

                        outfile.write('{};{};{};{}\n'.format(process, depare_region, rowValue, ii))
                        # rowPercentage = round(rowValue*100, 0)
                        #
                        # if depare_region in rowDict:
                        #     rowDict[depare_region] = rowDict[depare_region] + ';' + str(rowPercentage)
                        # else:
                        #     rowDict[depare_region] = depare_region + ';' + str(rowPercentage)
                        ii += 1
