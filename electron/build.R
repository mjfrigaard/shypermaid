# Build the desktop app. Run from the package root after scaffold_py.py.
library(shinyelectron)
app_check("electron/app")
res <- export(
  appdir    = "electron/app",
  destdir   = "electron/dist",
  overwrite = TRUE,
  sign      = nzchar(Sys.getenv("CSC_LINK")),
  run_after = interactive()
)
print(res)
