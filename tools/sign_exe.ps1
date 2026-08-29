$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=MiyooPlusSimulator" -CertStoreLocation "Cert:\CurrentUser\My"
$exePath = Join-Path (Get-Location) "windows\MiyooPlusSimulator.exe"
if (Test-Path $exePath) {
    Set-AuthenticodeSignature -Certificate $cert -FilePath $exePath
    Write-Host "MiyooPlusSimulator.exe signed successfully with certificate:" $cert.Thumbprint
}
