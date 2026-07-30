$env:DATABASE_URL = 'postgresql://neondb_owner:npg_wCkrIFD9L2Tt@ep-rough-shape-avypfnm7-pooler.c-11.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$projectDir = 'C:\Users\jquad\Documents\app-revista'
$scriptPath = Join-Path $projectDir 'scripts' 'update_embeddings_fastembed.py'
$logFile = Join-Path $projectDir 'logs' 'update_fastembed.log'

while ($true) {
    $proc = Start-Process -FilePath 'python' -ArgumentList '-u', $scriptPath, '--max-batches', '10' -RedirectStandardOutput $logFile -RedirectStandardError $logFile -PassThru -NoNewWindow
    $proc.WaitForExit()
    $exitCode = $proc.ExitCode
    Add-Content -Path $logFile -Value "[LOOP] Processo encerrou com codigo $exitCode. Reiniciando em 5s..."
    Start-Sleep -Seconds 5
}
