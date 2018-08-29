const {
  lstatSync,
  readdirSync,
  readFileSync,
  writeFileSync
} = require('fs')

const path = require('path')
const bluePrintsDirectory = '_Blueprints-apps'
const bluePrintAppDirectories = readdirSync(bluePrintsDirectory)
const ignore = ['.DS_Store', 'mass-pub']
const appIgnore = ['node_modules']
bluePrintAppDirectories.forEach(blueprintAppDirectoryName => {
  if (ignore.includes(blueprintAppDirectoryName)) return
  
  // console.log('blueprintAppDirectoryName', blueprintAppDirectoryName)
  
  try {
    const content = readFileSync(path.join(bluePrintsDirectory, blueprintAppDirectoryName, 'template-1.yaml'), 'utf8')
    writeFileSync(path.join(blueprintAppDirectoryName, 'template.yaml'), content, 'utf8')
  } catch (error) {
    console.log('No template-1.yaml in ' + blueprintAppDirectoryName)
  }
  // const bluePrintAppContents = readdirSync(blueprintAppDirectoryName)
  // bluePrintAppContents.forEach(appFile => {
  //   console.log(appFile)
  //   const content = readFileSync(path.join(blueprintAppDirectoryName, appFile), 'utf8')
  //   console.log(content)
  //   // writeFileSync(destFile, content, encoding || 'utf8')
  // })
  // console.log(bluePrintAppContents)
})