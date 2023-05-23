"use strict";
(self["webpackChunkjudaicalink_labs"] = self["webpackChunkjudaicalink_labs"] || []).push([["src_js_autocomplete_js"],{

/***/ "./src/js/autocomplete.js":
/*!********************************!*\
  !*** ./src/js/autocomplete.js ***!
  \********************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony import */ var jquery__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! jquery */ "./node_modules/jquery/dist/jquery-exposed.js");
/* harmony import */ var jquery__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(jquery__WEBPACK_IMPORTED_MODULE_0__);
// for the autocomplete function in cm_e_search


if (typeof availableTags !== 'undefined') {
  console.log(availableTags);
  $(function () {
    $("#entities").autocomplete({
      source: availableTags,
      minLength: 2
    });
  });
}

/***/ })

}]);
//# sourceMappingURL=src_js_autocomplete_js.bundle.js.map