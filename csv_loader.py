import os


def load_pointfile(pointFile, fileType, delimiter, xName='x', yName='y', dName='depth', flip=False):
    pointFilePath = os.path.normpath(os.path.join(os.getcwd(), pointFile))
    print(pointFilePath)

    if fileType == 'csv':

        with open(pointFile) as fi:

            lineNumber = 0
            for line in fi.readlines()[:10]:
                if line.startswith('\"SEP') or line.startswith('SEP'):
                    print('skipping excel separator')
                    continue
                if lineNumber == 0:
                    headerRow = [val.strip() for val in line.split(delimiter)]
                    xPlace = headerRow.index(xName)
                    yPlace = headerRow.index(yName)
                    dPlace = headerRow.index(dName)
                    lineNumber += 1
                    continue

                point = line.split(delimiter)
                if flip:
                    point = [float(point[xPlace]), float(point[yPlace]),
                             round(-1*float(point[dPlace])+18, 4)]
                elif not flip:
                    point = [float(point[xPlace]), float(point[yPlace]),
                             round(float(point[dPlace])+18, 4)]

    elif fileType == 'shapefile':
        print('> ShapeFile not supported yet.')


surveyData = '../Data/operatorimplications/survey_3857_m_geom.csv'


load_pointfile(surveyData, 'csv', delimiter=',', xName='X', yName='Y', dName='DEPTH', flip=False)
