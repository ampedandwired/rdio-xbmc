// Copyright 2012 Charles Blaxland
// This file is part of rdio-xbmc.
//
// rdio-xbmc is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// rdio-xbmc is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with rdio-xbmc.  If not, see <http://www.gnu.org/licenses/>.

var page = new WebPage();
var script_args = {}

page.settings.userAgent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.63 Safari/537.31';

page.onConsoleMessage = function(msg) {
  console.log(msg);
};

exports.init = function(args) {
  script_args.username = args[0]
  script_args.password = args[1]
  script_args.token = args[2];
};

exports.steps = {
  start: {
    execute: function() {
      console.log("************************** " + script_args);
      page.open("https://www.rdio.com/account/oauth1/authorize/?oauth_token=" + script_args.token);
    },

    complete: function() {
      return PhantomXbmc.elementExists(page, 'input[name=username]');
    },

    next: function() {
      return 'login';
    }
  },

  login: {

    execute: function() {
      page.evaluate(function(args) {
        document.querySelector('input[name=username]').value = args.username;
        document.querySelector('input[name=password]').value = args.password;
        var submitButton = document.querySelector('button[name=submit]');
        submitButton.removeAttribute('disabled');
        submitButton.click();
      }, script_args);
    },

    complete: function() {
      return page.evaluate(function() {
        return document.querySelector('div.error_message') || document.querySelector('span.oauth_button.allow');
      });
    },

    next: function() {
      var error_div = page.evaluate(function() {
        return document.querySelector('div.error_message');
      });

      if (error_div) {
        PhantomXbmc.result.error = error_div.innerHTML;
        return null;
      }

      return 'authorize';
    }
  },

  authorize: {

    execute: function() {
      PhantomXbmc.result = page.evaluate(function(args) {
        var authStateResult = $.ajax({
          url: "/api/1/getOAuth1State",
          type: "POST",
          async: false,
          data: {
            method: "getOAuth1State",
            token: args.token,
            _authorization_key: Env.currentUser.authorizationKey
          }
        });

        var authStateResponse = jQuery.parseJSON(authStateResult.responseText)
        var verifier = authStateResponse.result.verifier;

        $.ajax({
          url: "/api/1/approveOAuth1App",
          type: "POST",
          async: false,
          data: {
            method: "approveOAuth1App",
            token: args.token,
            verifier: verifier,
            _authorization_key: Env.currentUser.authorizationKey
          }
        });

        return { verifier: verifier, cookie: $.cookie("r") };
      }, script_args);

    },

    complete: function() {
      return true;
    },

    next: function() {
      return null;
    }
  }

}
