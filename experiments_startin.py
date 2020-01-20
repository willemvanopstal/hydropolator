import startin

print(help(startin.DT))

pts = []
pts.append([0.0, 0.0, 11.11])
pts.append([1.0, 0.0, 22.22])
pts.append([1.0, 1.0, 33.33])
pts.append([0.0, 1.0, 44])
pts.append([0.5, 0.49, 44])
pts.append([0.45, 0.69, 44])
# pts.append([-999.9, -999.9, -999.9])
pts.append([0.65, 0.49, 44])
# pts.append([-999.9, -999.9, -999.9])
pts.append([0.75, 0.29, 44])
pts.append([1.5, 1.49, 44])
pts.append([0.6, 0.2, 44])
pts.append([0.45, 0.4, 44])
pts.append([0.1, 0.8, 44])
# pts.append([-909, -1200, 33])

t = startin.DT()
t.insert(pts)

print(t.number_of_vertices(), t.number_of_triangles())
print(t.locate(1.01, 0.87))
for vId in t.locate(1, 0.87):
    print(t.all_vertices()[vId])
