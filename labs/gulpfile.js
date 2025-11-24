const { series, src, dest } = require('gulp');

// watch changes in src folder
function watch() {
  return src('search/static/css/*.css')
    .pipe(dest('dist'));

}

// copy bootstap's assets to static folder
function bootstrap() {
  const files = [
    'node_modules/bootstrap/dist/css/bootstrap.min.css',
    'node_modules/bootstrap/dist/js/bootstrap.min.js'
  ]
  return src(files).pipe(dest('search/static/_vendor/css/'))
}

// copy jquery's assets to static folder
function jquery() {
  const files = [
    'node_modules/jquery/dist/jquery.min.js'
  ]
  return src(files).pipe(dest('search/static/_vendor/js'))
}


const uglify = require('gulp-uglify');
const concat = require('gulp-concat');

// Task 3: minify blueimp's assets and save to /_vendor/
function blueimp() {
  const files = [
    'node_modules/blueimp-file-upload/js/vendor/jquery.ui.widget.js',
    'node_modules/blueimp-file-upload/js/jquery.iframe-transport.js',
    'node_modules/blueimp-file-upload/js/jquery.fileupload.js'
  ]
  return src(files).pipe(uglify())
                   .pipe(concat('jquery.fileupload.min.js'))
                   .pipe(dest('_vendor/'))
}

exports.default = series(bootstrap, jquery)