/*!
 * TheAdmin's Gruntfile
 * http://thetheme.io/theadmin
 * Copyright 2019 TheAdmin
 */

module.exports = function(grunt) {
  'use strict';

  var config = require('./package.json');
  const sass = require('node-sass');


  var autoprefixer = require('autoprefixer')({
    browsers: [
      'Chrome >= 45',
      'Firefox >= 40',
      'Edge >= 12',
      'Explorer >= 11',
      'iOS >= 9',
      'Safari >= 9',
      'Android 2.3',
      'Android >= 4',
      'Opera >= 30'
    ]
  });

  var filesArr = [];
  var contentJSON = "";
  var contentHTML = "";


  // Project configuration.
  grunt.initConfig({

    // Metadata.
    pkg: grunt.file.readJSON('package.json'),
    banner: '/*!\n' +
            ' * <%= pkg.banner_name %> v<%= pkg.version %> (<%= pkg.homepage %>)\n' +
            ' * Copyright <%= grunt.template.today("yyyy") %> <%= pkg.author %>\n' +
            ' * Licensed under the Themeforest Standard Licenses\n' +
            ' */\n',


    // Task configuration
    // -------------------------------------------------------------------------------


    // Complile SCSS
    //
    sass: {

      expanded: {
        options: {
          implementation: sass,
          sourceMap: true,
          outputStyle: 'expanded'
        },
        files: {
          'src/assets/css/app.css': 'src/pro_assets/css/scss/app.scss',
          'src/assets/css/style.css': 'src/pro_assets/css/style.scss'
        }
      },

      compressed: {
        options: {
          implementation: sass,
          sourceMap: true,
          outputStyle: 'compressed'
        },
        files: {
          'src/assets/css/app.min.css': 'src/pro_assets/css/scss/app.scss',
          'src/assets/css/style.min.css': 'src/pro_assets/css/style.scss'
        }
      },


      // Samples
      //
      job_expanded: {
        options: {
          implementation: sass,
          sourceMap: true,
          outputStyle: 'expanded'
        },
        files: {'src/samples/job/assets/css/style.css': 'src/samples/job/pro_assets/css/style.scss'}
      },

      job_compressed: {
        options: {
          implementation: sass,
          sourceMap: true,
          outputStyle: 'compressed'
        },
        files: {'src/samples/job/assets/css/style.min.css': 'src/samples/job/pro_assets/css/style.scss',}
      },




      invoicer_expanded: {
        options: {
          implementation: sass,
          sourceMap: true,
          outputStyle: 'expanded'
        },
        files: {'src/samples/invoicer/assets/css/style.css': 'src/samples/invoicer/pro_assets/css/style.scss'}
      },

      invoicer_compressed: {
        options: {
          implementation: sass,
          sourceMap: true,
          outputStyle: 'compressed'
        },
        files: {'src/samples/invoicer/assets/css/style.min.css': 'src/samples/invoicer/pro_assets/css/style.scss',}
      },




      support_expanded: {
        options: {
          implementation: sass,
          sourceMap: true,
          outputStyle: 'expanded'
        },
        files: {'src/samples/support/assets/css/style.css': 'src/samples/support/pro_assets/css/style.scss'}
      },

      support_compressed: {
        options: {
          implementation: sass,
          sourceMap: true,
          outputStyle: 'compressed'
        },
        files: {'src/samples/support/assets/css/style.min.css': 'src/samples/support/pro_assets/css/style.scss',}
      },


    },





    // Watch on SCSS files
    //
    watch: {
      sass: {
        files: ['src/pro_assets/css/**/*.scss'],
        tasks: ['sass:expanded', 'sass:compressed']
      },
      js: {
        files: ['src/pro_assets/js/src/**/*.js'],
        tasks: ['concat:appjs', 'uglify:app']
      },

      script: {
        files: ['src/pro_assets/js/script.js'],
        tasks: ['uglify:script']
      },

      script_dir: {
        files: ['src/pro_assets/js/script/*.js', 'src/pro_assets/js/script/**/*.js'],
        tasks: ['neuter:js']
      },

      // Samples
      job_sass: {
        files: ['src/samples/job/pro_assets/css/**/*.scss'],
        tasks: ['sass:job_compressed', 'sass:job_expanded']
      },
      job_js: {
        files: ['src/samples/job/pro_assets/js/*.js', '!src/samples/job/pro_assets/js/*.min.js'],
        tasks: ['uglify:job']
      },

      invoicer_sass: {
        files: ['src/samples/invoicer/pro_assets/css/**/*.scss'],
        tasks: ['sass:invoicer_compressed', 'sass:invoicer_expanded']
      },
      invoicer_js: {
        files: ['src/samples/invoicer/pro_assets/js/*.js', '!src/samples/invoicer/pro_assets/js/*.min.js'],
        tasks: ['uglify:invoicer']
      },

      support_sass: {
        files: ['src/samples/support/pro_assets/css/**/*.scss'],
        tasks: ['sass:support_compressed', 'sass:support_expanded']
      },
      support_js: {
        files: ['src/samples/support/pro_assets/js/*.js', '!src/samples/support/pro_assets/js/*.min.js'],
        tasks: ['uglify:support']
      },
    },





    // Browser Sync
    //
    browserSync: {
      dev: {
        bsFiles: {
          src : [
            'src/pro_assets/css/*.min.css',
            'src/pro_assets/js/*.min.js',
            'src/**/*.html',

            'src/samples/*/pro_assets/css/*.css',
            'src/samples/*/pro_assets/js/*.js',
            'src/samples/*/*.html'
          ]
        },
        options: {
          watchTask: true,
          server: "src"
        }
      }
    },





    // Clean files and directories
    //
    clean: {
      starter: [
        'starter/*/',
      ],

      starter_copied: [
        'starter/*/*/',
        '!starter/*/pro_assets/',
        'starter/*/pro_assets/css/scss/*',
        'starter/*/pro_assets/css/scss/*/',
        'starter/*/pro_assets/css/style*.map',
        'starter/*/pro_assets/data/**',
        'starter/*/pro_assets/js/src/**',
        'starter/*/pro_assets/js/script/**',
        'starter/*/pro_assets/js/script.*',
        'starter/*/pro_assets/img/*/',
      ],

      dist: [
        'dist/',
      ],

      dist_copied: [
        "dist/theme/src/pro_assets/img/**/*",
      ]
    },





    // Copy files
    //
    copy: {
      starter: {
        files: [
          {expand: true, cwd: 'src/pro_assets/', src: ['**'], dest: 'starter/src/pro_assets/'},
          {expand: true, cwd: 'src/page-extra/', src: ['blank.html'], dest: 'starter/src/'},
        ],
      },

      dist: {
        files: [
          {expand: true, cwd: 'src/', src: ['**'], dest: 'dist/theme/src'},
          {expand: true, cwd: '.', src: ['package.json', 'gruntfile.js'], dest: 'dist/theme'},
          {expand: true, cwd: 'starter/', src: ['**'], dest: 'dist/starter'},
          {expand: true, cwd: 'misc/', src: ['CHANGELOG.md', 'README.md'], dest: 'dist'},
          {expand: true, cwd: 'misc/', src: ['demo.html', 'documentation.html'], dest: 'dist'},
          {expand: true, cwd: '.', src: ['README.md'], dest: 'dist/theme'},

          /*
          {expand: true, cwd: 'src/', src: ['**'], dest: 'dist/demo/framework'},
          {expand: true, cwd: 'src/', src: ['**'], dest: 'dist/source/src'},
          {expand: true, cwd: 'src/samples/', src: ['**'], dest: 'dist/demo/samples'},
          {expand: true, cwd: 'starter/', src: ['**'], dest: 'dist/starter'},
          {expand: true, cwd: '.', src: ['package.json', 'gruntfile.js'], dest: 'dist/source'},
          {expand: true, cwd: 'grunt/demo/', src: ['**'], dest: 'dist/demo'},
          */
        ],
      },

      dev: {
        files: [
          {expand: true, cwd: 'src/pro_assets/vendor/font-awesome/fonts',  src: ['**'], dest: 'src/pro_assets/fonts/'},
          {expand: true, cwd: 'src/pro_assets/vendor/themify-icons/fonts', src: ['**'], dest: 'src/pro_assets/fonts/'},
        ]
      },

      placeholder: {
        files: [
          {expand: true, cwd: 'placeholders/', src: ['**'], dest: 'dist/theme/src/pro_assets/img'},
        ],
      }

    },





    // Concat plugins to make core.min
    //
    concat: {
      appjs: {
        files: {
          // Javascript
          'src/assets/js/app.js':
          [

            'src/pro_assets/js/src/jquery-extends.js',
            'src/pro_assets/js/src/app.js',

            // Providers
            'src/pro_assets/js/src/provider/provider.js',
            'src/pro_assets/js/src/provider/provider-list.js',
            'src/pro_assets/js/src/provider/chart.js',
            'src/pro_assets/js/src/provider/code.js',
            'src/pro_assets/js/src/provider/editor.js',
            'src/pro_assets/js/src/provider/emoji.js',
            'src/pro_assets/js/src/provider/form.js',
            'src/pro_assets/js/src/provider/icon.js',
            'src/pro_assets/js/src/provider/map.js',
            'src/pro_assets/js/src/provider/table.js',
            'src/pro_assets/js/src/provider/ui.js',
            'src/pro_assets/js/src/provider/upload.js',
            'src/pro_assets/js/src/provider/misc.js',

            // Plugnis
            'src/pro_assets/js/src/plugin/map.js',
            'src/pro_assets/js/src/plugin/modaler.js',
            'src/pro_assets/js/src/plugin/toast.js',

            // Components
            'src/pro_assets/js/src/component/aside.js',
            'src/pro_assets/js/src/component/topbar.js',
            'src/pro_assets/js/src/component/sidebar.js',
            'src/pro_assets/js/src/component/quickview.js',
            'src/pro_assets/js/src/component/dock.js',
            'src/pro_assets/js/src/component/topbar-menu.js',
            'src/pro_assets/js/src/component/lookup.js',
            'src/pro_assets/js/src/component/cards.js',


            'src/pro_assets/js/src/app-extra.js',
            'src/pro_assets/js/src/app-init.js'
          ]
        },
      },

      core: {
        files: {
          // Javascript
          'src/assets/js/core.min.js':
          [
            'src/pro_assets/vendor/pace/pace.min.js',
            'src/pro_assets/vendor/jquery/jquery.min.js',
            'src/pro_assets/vendor/popper/popper.min.js',
            'src/pro_assets/vendor/bootstrap/js/bootstrap.min.js',
            'src/pro_assets/vendor/lab/LAB.min.js',
            'src/pro_assets/vendor/jquery.hotkeys/jquery.hotkeys.js',
            'src/pro_assets/vendor/push/push.min.js',
            'src/pro_assets/vendor/animsition/js/animsition.min.js',
            'src/pro_assets/vendor/perfect-scrollbar/js/perfect-scrollbar.jquery.min.js',
          ],

          // CSS
          'src/assets/css/core.min.css':
          [
            'src/pro_assets/vendor/bootstrap/css/bootstrap.min.css',
            'src/pro_assets/vendor/font-awesome/css/font-awesome.min.css',
            'src/pro_assets/vendor/themify-icons/css/themify-icons.css',
            'src/pro_assets/vendor/animsition/css/animsition.min.css',
            'src/pro_assets/vendor/perfect-scrollbar/css/perfect-scrollbar.min.css',
          ]
        }
      }

    },




    // Import file for script.js
    //
    neuter: {
      options: {
        template: "{%= src %}"
      },
      js: {
        src: 'src/pro_assets/js/script/main.js',
        dest: 'src/pro_assets/js/script.js'
      },
      starter: {
        src: 'starter/src/pro_assets/js/script/main.js',
        dest: 'starter/src/pro_assets/js/script.js'
      }
    },




    // Uglify JS files
    //
    uglify: {
      options: {
        mangle: true,
        preserveComments: /^!|@preserve|@license|@cc_on/i,
        banner: '<%= banner %>'
      },
      app: {
        src:  'src/assets/js/app.js',
        dest: 'src/pro_assets/js/app.min.js'
      },
      core: {
        src:  'src/assets/js/core.min.js',
        dest: 'src/assets/js/core.min.js'
      },
      script: {
        src:  'src/pro_assets/js/script.js',
        dest: 'src/pro_assets/js/script.min.js'
      },
      starter: {
        src:  'starter/src/pro_assets/js/script.js',
        dest: 'starter/src/pro_assets/js/script.min.js'
      },

      // Samples
      job: {
        src:  'src/samples/job/pro_assets/js/script.js',
        dest: 'src/samples/job/pro_assets/js/script.min.js'
      },
      invoicer: {
        src:  'src/samples/invoicer/pro_assets/js/script.js',
        dest: 'src/samples/invoicer/pro_assets/js/script.min.js'
      },
      support: {
        src:  'src/samples/support/pro_assets/js/script.js',
        dest: 'src/samples/support/pro_assets/js/script.min.js'
      }
    },





    // CSS build configuration
    //
    scsslint: {
      options: {
        bundleExec: true,
        config: 'src/pro_assets/css/scss/.scss-lint.yml',
        reporterOutput: null
      },
      core: {
        src: ['src/pro_assets/css/scss/*.scss']
      }
    },





    // Do some post processing on CSS files
    //
    postcss: {
      options: {
        processors: [
          autoprefixer,
          require('postcss-flexbugs-fixes')
        ]
      },
      all: {
        src: ['src/pro_assets/css/*.css', '!src/pro_assets/css/core.min.css']
      },

      samples: {
        src: ['src/samples/*/pro_assets/css/*.css']
      }
    },





    // Minify CSS files
    //
    cssmin: {
      options: {
        //keepSpecialComments: '*',
        sourceMap: false,
        advanced:  false
      },
      core: {
        src:  'src/assets/css/core.min.css',
        dest: 'src/assets/css/core.min.css'
      },
      style: {
        src:  'src/assets/css/style.css',
        dest: 'src/assets/css/style.min.css'
      }
    },




    // Find and replace some texts
    //
    replace: {
      starter: {
        src: ['starter/src/blank.html'],
        overwrite: true,
        replacements: [{
          from: '../pro_assets/',
          to: 'pro_assets/'
        }]
      },

      samples: {
        src: ['dist/demo/samples/**/*.html'],
        overwrite: true,
        replacements: [{
          from: '../../pro_assets/',
          to: '../../framework/pro_assets/'
        }]
      },

      framework_nav: {
        src: ['dist/demo/framework/**/*.html'],
        overwrite: true,
        replacements: [{
          from: 'samples/',
          to: '../samples/'
        }]
      }
    },



    // Rename some files
    //
    rename: {
      starter: {
        files: [
          {src: ['starter/src/blank.html'], dest: 'starter/src/index_pro_dashboard.html'},
          {src: ['starter/src/pro_assets/js/script-starter'], dest: 'starter/src/pro_assets/js/script'},
          //{src: ['starter/src/pro_assets/js/script-starter.js'], dest: 'starter/src/pro_assets/js/script.js'},
          //{src: ['starter/src/pro_assets/js/script-starter.min.js'], dest: 'starter/src/pro_assets/js/script.min.js'},
        ]
      }
    },




    // Modify content of some files
    //
    rewrite: {
      starter_css: {
        src: 'starter/src/pro_assets/css/style*',
        editor: function(contents, filePath) {
          return '';
        }
      },
      samples: {
        src: 'dist/demo/samples/**/*.html',
        editor: function(contents, filePath) {
          return contents.replace(new RegExp('../../pro_assets/', 'g'), '../../framework/pro_assets/');
        }
      }
    },



    // Optimize image sizes
    //
    imagemin: {

      all: {
        files: [{
          expand: true,
          cwd: '.',
          src: [
            'src/pro_assets/img/**/*.{png,jpg,gif}',
            'placeholders/**/*.{png,jpg,gif}',
          ]
        }]
      }

    },



    // Grab some information from html files
    //
    dom_munger: {
      files_json: {
        options: {
          callback: function($, file){
            var title = $('head > title').text();
            var url   = file.substr(4); // Bypass "src/"
            var desc  = $('meta[name="description"]').attr('content');
            var keys  = $('meta[name="keywords"]').attr('content');

            var dir       = url.substr(0, url.indexOf('/'));
            var nextDir   = dir;
            var lastFile  = false;
            var lastClass = '';


            if ( title !== undefined ) {
              title = title.replace(' — TheAdmin', '');
            }


            if ( title.length < 1 ) {
              if ( filesArr.length > 0 ) {
                grunt.option('path', filesArr.shift());
                grunt.option('lastDir', dir);
              }
              return;
            }


            if ( keys !== undefined ) {
              keys = keys.replace(new RegExp(', ', 'g'), ' ');
              //keys = keys.split(',');
            }

            if ( filesArr.length > 0 ) {
              var path = filesArr[0].substr(4);
              nextDir = path.substr(0, path.indexOf('/'));
              if ( nextDir != dir ) {
                lastFile = true;
                lastClass = ' bb-0';
              }
            }



            var json_item = {
              "title": title,
              "url": url,
              "description": desc,
              "tokens": keys
            }

            contentJSON += JSON.stringify(json_item, null, 2) + ",\n";



            contentHTML += '  <a class="media media-vertical'+ lastClass +'" href="../'+ url +'">\n' +
                           '    <h6>'+ title +'</h6>\n' +
                           '     <small>'+ url +'</small>\n' +
                           '  </a>\n\n';

            if ( lastFile ) {
              contentHTML += '  <div class="divider text-uppercase fw-500 fs-10 ls-2 mb-0 mt-0">'+ nextDir +'</div>\n\n';
            }


            if ( filesArr.length == 2 ) {
              contentJSON = '[\n'+ contentJSON.substr(0, contentJSON.length - 2) + '\n]';
              grunt.file.write('src/pro_assets/data/json/files.json', contentJSON);

              contentHTML = '<div class="media-list media-list-xs media-list-hover media-list-divided">\n\n' + contentHTML + '</div>';
              grunt.file.write('src/pro_assets/data/pages-index_pro_dashboard.html', contentHTML);
            }
            else {
              grunt.option('path', filesArr.shift());
              grunt.option('lastDir', dir);
            }


          }
        },
        src: "<%= grunt.option('path') %>"
      },
    }


    // -------------------------------------------------------------------------------
    // END Task configuration

  });


  // These plugins provide necessary tasks.
  require('load-grunt-tasks')(grunt, { scope: 'devDependencies', pattern: ['grunt-*'] });
  require('autoprefixer')(grunt);
  //require('time-grunt')(grunt);

  // Run "grunt" to watch SCSS and JS files as well as running browser-sync
  grunt.registerTask('default', ['serve']);
  grunt.registerTask('dist', ['build']);
  grunt.registerTask('serve', ['browserSync', 'watch']);

  // Run "grunt build" to publish the template in a ./dist folder
  grunt.registerTask('build',
    [
      'clean:dist',
      'dev',
      'starter',
      'copy:dist',
      'clean:dist_copied',
      //'replace:samples',
      //'replace:framework_nav'
      'copy:placeholder'
    ]
  );


  // Run "grunt starter" to create starter template inside "./starter"
  grunt.registerTask('starter',
    [
      'clean:starter',
      'copy:starter',
      'replace:starter',
      'rewrite:starter_css',
      'clean:starter_copied',
      'rename:starter',
      'neuter:starter',
      'uglify:starter'
    ]
  );


  // Run "grunt dev" to make sure your CSS and JS files are up to date for development
  grunt.registerTask('dev',
    [
      'sass',
      'copy:dev',
      'concat',
      'uglify',
      'cssmin',
      'postcss'
    ]
  );



  // Generate files.json and pages-index_pro_dashboard.html
  grunt.registerTask('index', function(){
    var pattern = [
      //'src/*.html',
      'src/layout/*.html',
      'src/content/*.html',
      'src/extension/*.html',
      'src/uikit/*.html',
      'src/form/*.html',
      'src/chart/*.html',
      'src/widget/*.html',
      'src/page-app/*.html',
      'src/page/*.html',
      'src/page-extra/*.html',
      'src/email/*.html',
      'src/help/*.html',
    ];

    filesArr = grunt.file.expand(pattern);
    filesArr.forEach( function (file) {
      if ( file !== 'src/help/index_pro_dashboard.html' ) {
        grunt.option('path', filesArr.shift());
        grunt.option('lastDir', 'layout');
        grunt.task.run('dom_munger');
      }
    });

  });


};
