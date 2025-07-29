# Script PowerShell pour télécharger le modèle Mistral 7B (méthode sans token)
# Utilisation: .\download_mistral_local.ps1

Write-Host "🚀 TÉLÉCHARGEMENT DU MODÈLE MISTRAL 7B (MÉTHODE SANS TOKEN)" -ForegroundColor Blue
Write-Host "==========================================================" -ForegroundColor Blue

# Vérifier Git LFS
try {
    git lfs version | Out-Null
    Write-Host "✅ Git LFS disponible" -ForegroundColor Green
} catch {
    Write-Host "❌ Git LFS non installé" -ForegroundColor Red
    Write-Host "Installation de Git LFS..." -ForegroundColor Yellow
    winget install GitHub.GitLFS
    git lfs install
}

# Créer le dossier models
if (!(Test-Path "Docker\models")) {
    New-Item -ItemType Directory -Path "Docker\models" -Force
}

# Aller dans le dossier Docker
Set-Location Docker

# Vérifier si le modèle existe déjà
if ((Test-Path "models\mistral-7b") -and (Test-Path "models\mistral-7b\config.json")) {
    $size = (Get-ChildItem "models\mistral-7b" -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB
    Write-Host "✅ Modèle Mistral 7B déjà présent" -ForegroundColor Green
    Write-Host "📊 Taille: $([math]::Round($size, 2)) GB" -ForegroundColor Cyan
    Write-Host "🚀 Vous pouvez lancer: docker-compose up -d" -ForegroundColor Green
    exit 0
}

Write-Host "📥 Téléchargement du modèle Mistral 7B..." -ForegroundColor Yellow
Write-Host "⏳ Cela peut prendre 10-30 minutes selon votre connexion..." -ForegroundColor Yellow

# Cloner le modèle
try {
    git clone https://huggingface.co/mistralai/Mistral-7B-v0.1 models/mistral-7b
    
    Write-Host ""
    Write-Host "✅ Modèle Mistral 7B téléchargé avec succès!" -ForegroundColor Green
    $size = (Get-ChildItem "models\mistral-7b" -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB
    Write-Host "📊 Taille: $([math]::Round($size, 2)) GB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🚀 Vous pouvez maintenant lancer:" -ForegroundColor Green
    Write-Host "   cd Docker && docker-compose up -d" -ForegroundColor White
    Write-Host ""
    Write-Host "📁 Fichiers présents:" -ForegroundColor Cyan
    Get-ChildItem "models\mistral-7b" | Format-Table Name, Length
    
} catch {
    Write-Host "❌ Erreur lors du téléchargement: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} 