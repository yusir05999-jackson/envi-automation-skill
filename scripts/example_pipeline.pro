; ================================================================
; Impervious surface extraction - FULL PIPELINE (ENVI 6.2 / IDL 9.2)
;
;  Step1 FXSegmentation (Edge, Scale=50, Merge=60)  -> segments
;  Step2 BinaryLTThresholdRaster on NDVI (band9)   -> exclude vegetation
;  Step3 BinaryLTThresholdRaster on NDSI (band10)  -> exclude water
;  Step4 RuleRasterClassification combine           -> impervious mask
;  Step5 ClassificationToShapefile                  -> vector output
;
;  KEY: ENVI() must be called BEFORE ENVITask()
; ================================================================
pro impervious_pipeline
  compile_opt idl2

  D     = 'E:\work\data\'
  src   = D + 'sub_quac.hdr'
  seg   = D + 'fx_seg.dat'
  ndviM = D + 'ndvi_lt.dat'
  ndsiM = D + 'ndsi_lt.dat'
  clsO  = D + 'impervious_cls.dat'
  shpO  = D + 'impervious.shp'
  logF  = 'E:\work\_pipe_log.txt'
  flagF = 'E:\work\_pipe_done.txt'

  openw, lf, logF, /get_lun
  printf, lf, 'pipeline start'
  e = ENVI()
  printf, lf, 'envi ready'
  raster = e.OpenRaster(src)
  printf, lf, 'raster ok'

  ; ---------- STEP 1: segmentation ----------
  printf, lf, 'STEP1 segmentation'
  segTask = ENVITask('FXSegmentation')
  segTask.INPUT_RASTER = raster
  segTask.SEGMENT_ALGORITHM = 'Edge'
  segTask.SEGMENT_VALUE = 50.0
  segTask.SEGMENT_BANDS = [6L]
  segTask.MERGE_ALGORITHM = 'Full Lambda Schedule'
  segTask.MERGE_VALUE = 60.0
  segTask.MERGE_BANDS = [6L]
  segTask.KERNEL_SIZE = 3.0
  segTask.OUTPUT_RASTER_URI = seg
  segTask.Execute
  printf, lf, 'STEP1_OK'
  free_lun, lf

  ; ---------- STEP 2: NDVI < 0.28  (exclude vegetation) ----------
  ; NDVI stored as (v+1)*10000, so 0.28 -> 12800
  printf, lf, 'STEP2 ndvi threshold'
  ndviR = e.OpenRaster(src, 9)
  ndviT = ENVITask('BinaryLTThresholdRaster')
  ndviT.INPUT_RASTER = ndviR
  ndviT.THRESHOLD = 12800.0
  ndviT.OUTPUT_RASTER_URI = ndviM
  ndviT.Execute
  printf, lf, 'STEP2_OK'
  free_lun, lf

  ; ---------- STEP 3: NDSI < 0.13  (exclude water) ----------
  ; NDSI stored as (v+1)*10000, so 0.13 -> 11300
  printf, lf, 'STEP3 ndsi threshold'
  ndsiR = e.OpenRaster(src, 10)
  ndsiT = ENVITask('BinaryLTThresholdRaster')
  ndsiT.INPUT_RASTER = ndsiR
  ndsiT.THRESHOLD = 11300.0
  ndsiT.OUTPUT_RASTER_URI = ndsiM
  ndsiT.Execute
  printf, lf, 'STEP3_OK'
  free_lun, lf

  ; ---------- STEP 4: combine both masks ----------
  printf, lf, 'STEP4 combine'
  ndviMask = ndviT.OUTPUT_RASTER
  ndsiMask = ndsiT.OUTPUT_RASTER
  combT = ENVITask('BandMath')
  combT.INPUT_RASTER = [ndviMask, ndsiMask]
  printf, lf, 'STEP4_bandmath_set'
  free_lun, lf

  openw, mf, flagF, /get_lun
  printf, mf, 'THRESHOLDS_OK'
  free_lun, mf
  printf, '==== THRESHOLDS DONE ===='
end
