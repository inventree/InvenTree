import{bm as p,j as s,G as S,a1 as h,r as t,ao as v}from"./vendor-C5fHLTDD.js";import{g as c,u as d}from"./index-DX4YmBvQ.js";import{g as f}from"./BaseContext-BGXKB9QI.js";/**
 * @license @tabler/icons-react v3.1.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var x=c("outline","moon-stars","IconMoonStars",[["path",{d:"M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1 -8.313 -12.454z",key:"svg-0"}],["path",{d:"M17 4a2 2 0 0 0 2 2a2 2 0 0 0 -2 2a2 2 0 0 0 -2 -2a2 2 0 0 0 2 -2",key:"svg-1"}],["path",{d:"M19 11h2m-1 -1v2",key:"svg-2"}]]);/**
 * @license @tabler/icons-react v3.1.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var j=c("outline","sun","IconSun",[["path",{d:"M12 12m-4 0a4 4 0 1 0 8 0a4 4 0 1 0 -8 0",key:"svg-0"}],["path",{d:"M3 12h1m8 -9v1m8 8h1m-9 8v1m-6.4 -15.4l.7 .7m12.1 -.7l-.7 .7m0 11.4l.7 .7m-12.1 -.7l-.7 .7",key:"svg-1"}]]);function C(){const{colorScheme:n,toggleColorScheme:e}=p();return s.jsx(S,{position:"center",children:s.jsx(h,{onClick:()=>e(),size:"lg",sx:a=>({color:a.colorScheme==="dark"?a.colors.yellow[4]:a.colors.blue[6]}),children:n==="dark"?s.jsx(j,{}):s.jsx(x,{})})})}function b({width:n=80}){const[e,a]=t.useState(null),[l,u]=d(o=>[o.language,o.setLanguage]),[g,m]=t.useState([]);return t.useEffect(()=>{e!==null&&u(e)},[e]),t.useEffect(()=>{const o=f(),i=Object.keys(o).map(r=>({value:r,label:o[r]}));m(i),a(l)},[l]),s.jsx(v,{w:n,data:g,value:e,onChange:a,searchable:!0,"aria-label":"Select language"})}export{C,b as L};
