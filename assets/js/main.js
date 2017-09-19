/*
 * Main Javascript file for kojak_flask.
 *
 * This file bundles all of your javascript together using webpack.
 */

// JavaScript modules
require('jquery');
require('font-awesome-webpack');
require('bootstrap');
require('displacy-ent');
    

// Your own code
require('./plugins.js');
require('./script.js');
require('./editor.js');

