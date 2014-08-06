from __main__ import vtk, qt, ctk, slicer
import string
import numpy
import math
import operator

class GeometricalMeasures:
  
  def __init__(self, labelNode, parameterMatrix, parameterMatrixCoordinates, parameterValues, allKeys):
    # need non-linear scaling of surface heights for normalization
      
    self.GeometricalMeasures = {}
    self.GeometricalMeasures["Extruded Surface Area"] = "self.extrudedSurfaceArea(self.labelNode, self.extrudedMatrix, self.extrudedMatrixCoordinates, self.parameterValues)"
    self.GeometricalMeasures["Extruded Volume"] = "self.extrudedVolume(self.extrudedMatrix, self.extrudedMatrixCoordinates, self.cubicMMPerVoxel)"
    self.GeometricalMeasures["Extruded Surface:Volume Ratio"] = "self.extrudedSurfaceVolumeRatio(self.labelNode, self.extrudedMatrix, self.extrudedMatrixCoordinates, self.parameterValues, self.cubicMMPerVoxel)"
       
    self.labelNode = labelNode
    self.parameterMatrix = parameterMatrix
    self.parameterMatrixCoordinates = parameterMatrixCoordinates
    self.parameterValues = parameterValues
    self.keys = set(allKeys).intersection(self.GeometricalMeasures.keys())
    
    self.cubicMMPerVoxel = reduce(lambda x,y: x*y, self.labelNode.GetSpacing())
    self.extrudedMatrix, self.extrudedMatrixCoordinates = self.extrudeMatrix(self.parameterMatrix, self.parameterMatrixCoordinates, self.parameterValues)
    
  def extrudedSurfaceArea(self, labelNode, a, extrudedMatrixCoordinates, parameterValues):
    x, y, z = labelNode.GetSpacing()
       
    # surface areas of directional connections
    xz = x*z
    yz = y*z
    xy = x*y
    fourD = (2*xy + 2*xz + 2*yz)
    
    voxelTotalSA = (2*xy + 2*xz + 2*yz)
    totalSA = parameterValues.size * voxelTotalSA
    totalDimensionalSurfaceArea = (2*xy + 2*xz + 2*yz + 2*fourD)
    
    # in matrixSACoordinates
    # i: height (z), j: vertical (y), k: horizontal (x), l: 4th or extrusion dimension   
    i, j, k, l = 0, 0, 0, 0
    extrudedSurfaceArea = 0
    
    # vectorize
    for i,j,k,l_slice in zip(*extrudedMatrixCoordinates):
      for l in xrange(l_slice.start, l_slice.stop):
        fxy = numpy.array([ a[i+1,j,k,l], a[i-1,j,k,l] ]) == 0
        fyz = numpy.array([ a[i,j+1,k,l], a[i,j-1,k,l] ]) == 0
        fxz = numpy.array([ a[i,j,k+1,l], a[i,j,k-1,l] ]) == 0  
        f4d = numpy.array([ a[i,j,k,l+1], a[i,j,k,l-1] ]) == 0
               
        extrudedElementSurface = (numpy.sum(fxz) * xz) + (numpy.sum(fyz) * yz) + (numpy.sum(fxy) * xy) + (numpy.sum(f4d) * fourD)     
        extrudedSurfaceArea += extrudedElementSurface
    return (extrudedSurfaceArea)
  
  def extrudedVolume(self, extrudedMatrix, extrudedMatrixCoordinates, cubicMMPerVoxel):
    extrudedElementsSize = extrudedMatrix[numpy.where(extrudedMatrix == 1)].size
    return(extrudedElementsSize * cubicMMPerVoxel)
      
  def extrudedSurfaceVolumeRatio(self, labelNode, extrudedMatrix, extrudedMatrixCoordinates, parameterValues, cubicMMPerVoxel):
    extrudedSurfaceArea = self.extrudedSurfaceArea(labelNode, extrudedMatrix, extrudedMatrixCoordinates, parameterValues) 
    extrudedVolume = self.extrudedVolume(extrudedMatrix, extrudedMatrixCoordinates, cubicMMPerVoxel)    
    return(extrudedSurfaceArea/extrudedVolume)
    
  def extrudeMatrix(self, parameterMatrix, parameterMatrixCoordinates, parameterValues):
    # extrude 3D image into a binary 4D array with the intensity or parameter value as the 4th Dimension
    
    # maximum intensity/parameter value appended as shape of 4th dimension    
    extrudedShape = parameterMatrix.shape + (numpy.max(parameterValues),)
    
    # pad shape by 1 unit in all 8 directions
    extrudedShape = tuple(map(operator.add, extrudedShape, [2,2,2,2]))
    
    extrudedMatrix = numpy.zeros(extrudedShape)   
    extrudedMatrixCoordinates = tuple(map(operator.add, parameterMatrixCoordinates, ([1,1,1]))) + (numpy.array([slice(1,value+1) for value in parameterValues]),)   
    for slice4D in zip(*extrudedMatrixCoordinates):
      extrudedMatrix[slice4D] = 1      
    return (extrudedMatrix, extrudedMatrixCoordinates)
    
  def EvaluateFeatures(self):
    # Evaluate dictionary elements corresponding to user-selected keys 
    if not self.keys:
      return(self.GeometricalMeasures)
      
    for key in self.keys:
      self.GeometricalMeasures[key] = eval(self.GeometricalMeasures[key])
    return(self.GeometricalMeasures)    


