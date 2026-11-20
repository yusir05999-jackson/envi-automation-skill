pro segment_task
  compile_opt idl2

  src = 'E:\work\data\sub_quac.hdr'
  seg = 'E:\work\seg.dat'

  if file_search(seg) ne '' then file_delete, seg   ; ENVI refuses to overwrite an existing output

  e = ENVI()
  raster = e.OpenRaster(src)

  task = ENVITask('FXSegmentation')
  task.INPUT_RASTER   = raster
  task.SEGMENT_ALGORITHM = 'Edge'              ; or 'Quadtree'
  task.SEGMENT_VALUE  = 50.0                   ; segmentation scale
  task.SEGMENT_BANDS  = [6L]                   ; NIR1
  task.MERGE_ALGORITHM = 'Full Lambda Schedule'
  task.MERGE_VALUE    = 60.0                   ; merge scale
  task.MERGE_BANDS    = [6L]
  task.KERNEL_SIZE    = 3.0
  task.OUTPUT_RASTER_URI = seg

  task.Execute
  e.Close
end
