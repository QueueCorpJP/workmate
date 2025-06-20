const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const inputFile = path.join(__dirname, '../public/og-image.svg');
const outputFile = path.join(__dirname, '../public/og-image.png');

sharp(inputFile)
  .resize(1200, 630)
  .png()
  .toFile(outputFile)
  .then(() => {
    console.log('OGP画像の生成が完了しました');
  })
  .catch(err => {
    console.error('エラーが発生しました:', err);
  }); 