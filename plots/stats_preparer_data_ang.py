import os

keyword = 'ang'
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

headerRow = 'process;interval;aandeel;intervalindex'
rowDict = {}

with open('stats_together_data_ang.csv', 'w') as outfile:
    outfile.write(headerRow + '\n')

    for process in sortedProcesses:
        print(process)
        totalAngles = 0

        with open(depare_files[process]) as infile:

            lines = infile.readlines()

            for line in lines:
                if not line.startswith('SEP'):
                    rowEntry = line.split(separator)
                    if rowEntry[0] == 'sharps':
                        continue
                    else:
                        rowValue = int(rowEntry[-1].strip())
                        totalAngles += rowValue
                        # print(rowValue, totalAngles)

            print("totalAngles: ", totalAngles)

            ii = 0
            for line in lines:
                if not line.startswith('SEP'):
                    rowEntry = line.split(separator)
                    if rowEntry[0] == 'sharps':
                        continue
                    else:
                        rowValue = int(rowEntry[-1].strip())
                        depare_region = rowEntry[0]
                        rowValue = float(rowEntry[-1].strip().replace(',', '.'))
                        rowPercentage = round(rowValue / totalAngles, 4)
                        print(rowPercentage)

                        outfile.write('{};{};{};{}\n'.format(
                            process, depare_region, rowPercentage, ii))
                        # rowPercentage = round(rowValue*100, 0)
                        #
                        # if depare_region in rowDict:
                        #     rowDict[depare_region] = rowDict[depare_region] + ';' + str(rowPercentage)
                        # else:
                        #     rowDict[depare_region] = depare_region + ';' + str(rowPercentage)
                        ii += 1
