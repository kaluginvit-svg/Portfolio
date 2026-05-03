$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$root = Split-Path -Parent $PSScriptRoot
$output = Join-Path $root 'architecture.png'

$width = 1600
$height = 1000
$bitmap = New-Object System.Drawing.Bitmap $width, $height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.Clear([System.Drawing.Color]::White)

$font = New-Object System.Drawing.Font('Arial', 18, [System.Drawing.FontStyle]::Regular)
$titleFont = New-Object System.Drawing.Font('Arial', 28, [System.Drawing.FontStyle]::Bold)
$smallFont = New-Object System.Drawing.Font('Arial', 14, [System.Drawing.FontStyle]::Regular)
$pen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(70, 100, 130), 3)
$textBrush = [System.Drawing.Brushes]::Black
$blueBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(235, 243, 255))
$greenBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(235, 250, 240))
$grayBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(245, 245, 245))

function Draw-Box {
    param(
        [int]$X,
        [int]$Y,
        [int]$Width,
        [int]$Height,
        [string]$Label,
        [System.Drawing.Brush]$Brush
    )

    $rect = New-Object System.Drawing.Rectangle $X, $Y, $Width, $Height
    $rectF = New-Object System.Drawing.RectangleF ([float]$X), ([float]$Y), ([float]$Width), ([float]$Height)
    $graphics.FillRectangle($Brush, $rect)
    $graphics.DrawRectangle($pen, $rect)

    $format = New-Object System.Drawing.StringFormat
    $format.Alignment = [System.Drawing.StringAlignment]::Center
    $format.LineAlignment = [System.Drawing.StringAlignment]::Center
    $graphics.DrawString($Label, $font, $textBrush, $rectF, $format)
}

function Draw-Arrow {
    param([int]$X1, [int]$Y1, [int]$X2, [int]$Y2)

    $arrowPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(70, 100, 130), 3)
    $arrowPen.CustomEndCap = New-Object System.Drawing.Drawing2D.AdjustableArrowCap 6, 6
    $graphics.DrawLine($arrowPen, $X1, $Y1, $X2, $Y2)
    $arrowPen.Dispose()
}

$graphics.DrawString('Team AI Bot Architecture', $titleFont, $textBrush, 40, 30)

Draw-Box 60 180 240 90 'Telegram Chat' $blueBrush
Draw-Box 380 180 260 90 'PyTelegramBotAPI Bot' $blueBrush
Draw-Box 720 80 260 90 'Session Manager' $grayBrush
Draw-Box 720 280 280 90 'Message Normalizer' $grayBrush
Draw-Box 1080 280 300 90 'Haystack Indexing Pipeline' $blueBrush
Draw-Box 1080 500 300 90 'Haystack Query Pipeline' $blueBrush
Draw-Box 720 690 320 90 'Haystack Summarization Pipeline' $blueBrush
Draw-Box 1080 80 260 90 'OpenAI Embeddings' $greenBrush
Draw-Box 1420 280 140 310 'Pinecone Index' $greenBrush
Draw-Box 1080 690 260 90 'OpenAI Chat Generator' $greenBrush
Draw-Box 1360 690 200 90 'Summary Decisions Action Items' $greenBrush
Draw-Box 1080 850 260 80 'Context Answer' $greenBrush

Draw-Arrow 300 225 380 225
Draw-Arrow 640 225 720 125
Draw-Arrow 640 225 720 325
Draw-Arrow 1000 325 1080 325
Draw-Arrow 1380 325 1420 360
Draw-Arrow 1210 280 1210 170
Draw-Arrow 1340 125 1420 320
Draw-Arrow 640 225 1080 545
Draw-Arrow 1380 545 1420 500
Draw-Arrow 1160 590 1160 850
Draw-Arrow 1040 735 1080 735
Draw-Arrow 1340 735 1360 735
Draw-Arrow 980 125 1080 125
Draw-Arrow 640 225 720 735

$graphics.DrawString('start / stop / status', $smallFont, $textBrush, 675, 100)
$graphics.DrawString('messages + metadata', $smallFont, $textBrush, 760, 250)
$graphics.DrawString('RAG search', $smallFont, $textBrush, 1030, 470)
$graphics.DrawString('final summary', $smallFont, $textBrush, 1040, 660)

$bitmap.Save($output, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()

Write-Host "Saved $output"
