(function(e){function t(t){for(var s,r,i=t[0],o=t[1],j=t[2],l=0,f=[];l<i.length;l++)r=i[l],Object.prototype.hasOwnProperty.call(c,r)&&c[r]&&f.push(c[r][0]),c[r]=0;for(s in o)Object.prototype.hasOwnProperty.call(o,s)&&(e[s]=o[s]);b&&b(t);while(f.length)f.shift()();return a.push.apply(a,j||[]),n()}function n(){for(var e,t=0;t<a.length;t++){for(var n=a[t],s=!0,i=1;i<n.length;i++){var o=n[i];0!==c[o]&&(s=!1)}s&&(a.splice(t--,1),e=r(r.s=n[0]))}return e}var s={},c={app:0},a=[];function r(t){if(s[t])return s[t].exports;var n=s[t]={i:t,l:!1,exports:{}};return e[t].call(n.exports,n,n.exports,r),n.l=!0,n.exports}r.m=e,r.c=s,r.d=function(e,t,n){r.o(e,t)||Object.defineProperty(e,t,{enumerable:!0,get:n})},r.r=function(e){"undefined"!==typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},r.t=function(e,t){if(1&t&&(e=r(e)),8&t)return e;if(4&t&&"object"===typeof e&&e&&e.__esModule)return e;var n=Object.create(null);if(r.r(n),Object.defineProperty(n,"default",{enumerable:!0,value:e}),2&t&&"string"!=typeof e)for(var s in e)r.d(n,s,function(t){return e[t]}.bind(null,s));return n},r.n=function(e){var t=e&&e.__esModule?function(){return e["default"]}:function(){return e};return r.d(t,"a",t),t},r.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},r.p="/";var i=window["webpackJsonp"]=window["webpackJsonp"]||[],o=i.push.bind(i);i.push=t,i=i.slice();for(var j=0;j<i.length;j++)t(i[j]);var b=o;a.push([0,"chunk-vendors"]),n()})({0:function(e,t,n){e.exports=n("56d7")},4678:function(e,t,n){var s={"./af":"2bfb","./af.js":"2bfb","./ar":"8e73","./ar-dz":"a356","./ar-dz.js":"a356","./ar-kw":"423e","./ar-kw.js":"423e","./ar-ly":"1cfd","./ar-ly.js":"1cfd","./ar-ma":"0a84","./ar-ma.js":"0a84","./ar-sa":"8230","./ar-sa.js":"8230","./ar-tn":"6d83","./ar-tn.js":"6d83","./ar.js":"8e73","./az":"485c","./az.js":"485c","./be":"1fc1","./be.js":"1fc1","./bg":"84aa","./bg.js":"84aa","./bm":"a7fa","./bm.js":"a7fa","./bn":"9043","./bn-bd":"9686","./bn-bd.js":"9686","./bn.js":"9043","./bo":"d26a","./bo.js":"d26a","./br":"6887","./br.js":"6887","./bs":"2554","./bs.js":"2554","./ca":"d716","./ca.js":"d716","./cs":"3c0d","./cs.js":"3c0d","./cv":"03ec","./cv.js":"03ec","./cy":"9797","./cy.js":"9797","./da":"0f14","./da.js":"0f14","./de":"b469","./de-at":"b3eb","./de-at.js":"b3eb","./de-ch":"bb71","./de-ch.js":"bb71","./de.js":"b469","./dv":"598a","./dv.js":"598a","./el":"8d47","./el.js":"8d47","./en-au":"0e6b","./en-au.js":"0e6b","./en-ca":"3886","./en-ca.js":"3886","./en-gb":"39a6","./en-gb.js":"39a6","./en-ie":"e1d3","./en-ie.js":"e1d3","./en-il":"7333","./en-il.js":"7333","./en-in":"ec2e","./en-in.js":"ec2e","./en-nz":"6f50","./en-nz.js":"6f50","./en-sg":"b7e9","./en-sg.js":"b7e9","./eo":"65db","./eo.js":"65db","./es":"898b","./es-do":"0a3c","./es-do.js":"0a3c","./es-mx":"b5b7","./es-mx.js":"b5b7","./es-us":"55c9","./es-us.js":"55c9","./es.js":"898b","./et":"ec18","./et.js":"ec18","./eu":"0ff2","./eu.js":"0ff2","./fa":"8df4","./fa.js":"8df4","./fi":"81e9","./fi.js":"81e9","./fil":"d69a","./fil.js":"d69a","./fo":"0721","./fo.js":"0721","./fr":"9f26","./fr-ca":"d9f8","./fr-ca.js":"d9f8","./fr-ch":"0e49","./fr-ch.js":"0e49","./fr.js":"9f26","./fy":"7118","./fy.js":"7118","./ga":"5120","./ga.js":"5120","./gd":"f6b4","./gd.js":"f6b4","./gl":"8840","./gl.js":"8840","./gom-deva":"aaf2","./gom-deva.js":"aaf2","./gom-latn":"0caa","./gom-latn.js":"0caa","./gu":"e0c5","./gu.js":"e0c5","./he":"c7aa","./he.js":"c7aa","./hi":"dc4d","./hi.js":"dc4d","./hr":"4ba9","./hr.js":"4ba9","./hu":"5b14","./hu.js":"5b14","./hy-am":"d6b6","./hy-am.js":"d6b6","./id":"5038","./id.js":"5038","./is":"0558","./is.js":"0558","./it":"6e98","./it-ch":"6f12","./it-ch.js":"6f12","./it.js":"6e98","./ja":"079e","./ja.js":"079e","./jv":"b540","./jv.js":"b540","./ka":"201b","./ka.js":"201b","./kk":"6d79","./kk.js":"6d79","./km":"e81d","./km.js":"e81d","./kn":"3e92","./kn.js":"3e92","./ko":"22f8","./ko.js":"22f8","./ku":"2421","./ku.js":"2421","./ky":"9609","./ky.js":"9609","./lb":"440c","./lb.js":"440c","./lo":"b29d","./lo.js":"b29d","./lt":"26f9","./lt.js":"26f9","./lv":"b97c","./lv.js":"b97c","./me":"293c","./me.js":"293c","./mi":"688b","./mi.js":"688b","./mk":"6909","./mk.js":"6909","./ml":"02fb","./ml.js":"02fb","./mn":"958b","./mn.js":"958b","./mr":"39bd","./mr.js":"39bd","./ms":"ebe4","./ms-my":"6403","./ms-my.js":"6403","./ms.js":"ebe4","./mt":"1b45","./mt.js":"1b45","./my":"8689","./my.js":"8689","./nb":"6ce3","./nb.js":"6ce3","./ne":"3a39","./ne.js":"3a39","./nl":"facd","./nl-be":"db29","./nl-be.js":"db29","./nl.js":"facd","./nn":"b84c","./nn.js":"b84c","./oc-lnc":"167b","./oc-lnc.js":"167b","./pa-in":"f3ff","./pa-in.js":"f3ff","./pl":"8d57","./pl.js":"8d57","./pt":"f260","./pt-br":"d2d4","./pt-br.js":"d2d4","./pt.js":"f260","./ro":"972c","./ro.js":"972c","./ru":"957c","./ru.js":"957c","./sd":"6784","./sd.js":"6784","./se":"ffff","./se.js":"ffff","./si":"eda5","./si.js":"eda5","./sk":"7be6","./sk.js":"7be6","./sl":"8155","./sl.js":"8155","./sq":"c8f3","./sq.js":"c8f3","./sr":"cf1e","./sr-cyrl":"13e9","./sr-cyrl.js":"13e9","./sr.js":"cf1e","./ss":"52bd","./ss.js":"52bd","./sv":"5fbd","./sv.js":"5fbd","./sw":"74dc","./sw.js":"74dc","./ta":"3de5","./ta.js":"3de5","./te":"5cbb","./te.js":"5cbb","./tet":"576c","./tet.js":"576c","./tg":"3b1b","./tg.js":"3b1b","./th":"10e8","./th.js":"10e8","./tk":"5aff","./tk.js":"5aff","./tl-ph":"0f38","./tl-ph.js":"0f38","./tlh":"cf75","./tlh.js":"cf75","./tr":"0e81","./tr.js":"0e81","./tzl":"cf51","./tzl.js":"cf51","./tzm":"c109","./tzm-latn":"b53d","./tzm-latn.js":"b53d","./tzm.js":"c109","./ug-cn":"6117","./ug-cn.js":"6117","./uk":"ada2","./uk.js":"ada2","./ur":"5294","./ur.js":"5294","./uz":"2e8c","./uz-latn":"010e","./uz-latn.js":"010e","./uz.js":"2e8c","./vi":"2921","./vi.js":"2921","./x-pseudo":"fd7e","./x-pseudo.js":"fd7e","./yo":"7f33","./yo.js":"7f33","./zh-cn":"5c3a","./zh-cn.js":"5c3a","./zh-hk":"49ab","./zh-hk.js":"49ab","./zh-mo":"3a6c","./zh-mo.js":"3a6c","./zh-tw":"90ea","./zh-tw.js":"90ea"};function c(e){var t=a(e);return n(t)}function a(e){if(!n.o(s,e)){var t=new Error("Cannot find module '"+e+"'");throw t.code="MODULE_NOT_FOUND",t}return s[e]}c.keys=function(){return Object.keys(s)},c.resolve=a,e.exports=c,c.id="4678"},"56d7":function(e,t,n){"use strict";n.r(t);n("e260"),n("e6cf"),n("cca6"),n("a79d");var s=n("7a23");function c(e,t,n,c,a,r){var i=Object(s["F"])("Ping");return Object(s["A"])(),Object(s["j"])(i)}n("b680");var a=Object(s["l"])("h2",{style:{"margin-top":"20px"}}," Sample News Article ",-1),r={style:{background:"#ececec",padding:"30px"}},i={style:{"margin-top":"20px"}};function o(e,t,n,c,o,j){var b=Object(s["F"])("a-tag"),l=Object(s["F"])("a-select-option"),f=Object(s["F"])("a-select"),u=Object(s["F"])("a-spin"),d=Object(s["F"])("a-list-item"),p=Object(s["F"])("a-list"),h=Object(s["G"])("value");return Object(s["A"])(),Object(s["j"])(s["b"],null,[a,Object(s["l"])("div",null,[Object(s["l"])(u,{spinning:e.spinning1},{default:Object(s["O"])((function(){return[Object(s["l"])("div",r,[Object(s["l"])("p",{innerHTML:o.entity_html},null,8,["innerHTML"]),(Object(s["A"])(!0),Object(s["j"])(s["b"],null,Object(s["E"])(o.entities,(function(t,n){return Object(s["A"])(),Object(s["j"])("div",{key:n},[Object(s["l"])(b,{color:"orange",style:{width:"20%"}},{default:Object(s["O"])((function(){return[Object(s["k"])(Object(s["H"])(n),1)]})),_:2},1024),Object(s["l"])(f,{style:{width:"50%"},onFocus:e.focus,ref:"select",allowClear:"true",onChange:j.handleChange,value:o.entity_abstraction[n],"onUpdate:value":function(e){return o.entity_abstraction[n]=e}},{default:Object(s["O"])((function(){return[(Object(s["A"])(!0),Object(s["j"])(s["b"],null,Object(s["E"])(t,(function(e){return Object(s["P"])((Object(s["A"])(),Object(s["j"])(l,{key:e["id"]},{default:Object(s["O"])((function(){return[Object(s["k"])(Object(s["H"])(e["id"])+" "+Object(s["H"])(e["count"])+" "+Object(s["H"])(e["kg_score"].toFixed(2)),1)]})),_:2},1536)),[[h,e["id"]]])})),128))]})),_:2},1032,["onFocus","onChange","value","onUpdate:value"])])})),128))])]})),_:1},8,["spinning"]),Object(s["l"])("h3",i," Similar News from abstractions (count: "+Object(s["H"])(o.news_list.length)+")",1),Object(s["l"])(u,{spinning:o.spinning},{default:Object(s["O"])((function(){return[Object(s["l"])(p,{style:{padding:"100px"},"item-layout":"vertical","data-source":o.news_list},{renderItem:Object(s["O"])((function(e){var t=e.item;return[Object(s["l"])(d,null,{actions:Object(s["O"])((function(){return[Object(s["l"])("a",{onClick:function(e){return j.getMessage(t)}},"view detail",8,["onClick"])]})),default:Object(s["O"])((function(){return[Object(s["l"])("div",{innerHTML:t.entity_html},null,8,["innerHTML"]),(Object(s["A"])(!0),Object(s["j"])(s["b"],null,Object(s["E"])(t.abstractions,(function(e){return Object(s["A"])(),Object(s["j"])(b,{key:e,color:"pink"},{default:Object(s["O"])((function(){return[Object(s["k"])(Object(s["H"])(e),1)]})),_:2},1024)})),128))]})),_:2},1024)]})),_:1},8,["data-source"])]})),_:1},8,["spinning"])])],64)}var j=n("2909"),b=(n("d3b7"),n("25f0"),n("07ac"),n("4de4"),n("6062"),n("3ca3"),n("ddb0"),n("bc3a")),l=n.n(b),f={name:"Ping",data:function(){return{msg:"",entity_html:"",entities:[],entity_abstraction:{},news_list:[],spinning:!1,id:null}},computed:{console:function(e){function t(){return e.apply(this,arguments)}return t.toString=function(){return e.toString()},t}((function(){return console})),window:function(e){function t(){return e.apply(this,arguments)}return t.toString=function(){return e.toString()},t}((function(){return window}))},methods:{handleChange:function(e){console.log("selected"),console.log(e),console.log(this.entity_abstraction),console.log(Object.values(this.entity_abstraction)),this.searchNewsByAbstractions()},getMessage:function(e){var t=this;console.log(e),e&&(this.id=e.id),this.spinning1=!0;var n="/ping";l.a.get(this.id?n+"/"+this.id:n).then((function(e){console.log(e),t.spinning1=!1;var n=e.data;for(var s in console.log(n),t.id=n["id"],t.msg=n["url"],t.entity_html=n.entity_html,t.entities=n.entities,t.entities)t.entity_abstraction[s]=t.entities[s][0]["id"];console.log(t.entity_abstraction),t.searchNewsByAbstractions()})).catch((function(e){console.error(e),t.spinning1=!1}))},searchNewsByAbstractions:function(){var e=this;this.spinning=!0;var t="/search_news_by_abstractions",n=Object.values(this.entity_abstraction);n=n.filter((function(e){return e})),n=Object(j["a"])(new Set(n)),console.log(n),l.a.post(t,{news_ids_to_exclude:[this.id],abstractions:n}).then((function(t){console.log(t);var n=t.data;console.log(n),e.news_list=n,e.spinning=!1})).catch((function(t){console.error(t),e.spinning=!1}))}},created:function(){this.getMessage()}};f.render=o;var u=f,d={name:"App",components:{Ping:u}};n("f506");d.render=c;var p=d,h=n("f23d"),g=(n("202f"),Object(s["i"])(p));g.config.productionTip=!1,g.use(h["a"]),g.mount("#app")},a93b:function(e,t,n){},f506:function(e,t,n){"use strict";n("a93b")}});
//# sourceMappingURL=app.f520d414.js.map