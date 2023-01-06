$flagfile = "C:\Users\vagrant\Documents\01_dev\rmkv2\agent\tmp" + "\rmktest_flagfile"
$nul > $flagfile
Start-Sleep -Seconds 5
Remove-Item $flagfile
