var page = new WebPage();
page.settings.userAgent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.63 Safari/537.31';

page.onConsoleMessage = function(msg) {
  console.log(msg);
};

exports.init = function(script_args) {
  token = script_args[0];
};

exports.steps = {
  start: {
    execute: function() {
      page.open("https://www.rdio.com/account/oauth1/authorize/?oauth_token=" + token);
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
      page.evaluate(function() {
        document.querySelector('input[name=username]').value = 'charles.blaxland@gmail.com';
        document.querySelector('input[name=password]').value = 'slsMcr4YqMloccqBvjc0';
        var submitButton = document.querySelector('button[name=submit]');
        submitButton.removeAttribute('disabled');
        submitButton.click();
      });
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
      PhantomXbmc.result = page.evaluate(function(token) {
        var authStateResult = $.ajax({
          url: "/api/1/getOAuth1State",
          type: "POST",
          async: false,
          data: {
            method: "getOAuth1State",
            token: token,
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
            token: token,
            verifier: verifier,
            _authorization_key: Env.currentUser.authorizationKey
          }
        });

        return { verifier: verifier, cookie: $.cookie("r") };
      }, token);

    },

    complete: function() {
      return true;
    },

    next: function() {
      return null;
    }
  }

}
