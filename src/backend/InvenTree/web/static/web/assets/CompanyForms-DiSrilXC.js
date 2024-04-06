import{r as t,j as e}from"./vendor-C5fHLTDD.js";import{g as u}from"./index-DX4YmBvQ.js";import{j as l,k as p,l as m,m as f}from"./ApiForm-Dtyf-xF2.js";import{I as d}from"./IconAt-DPf0GkPm.js";import{I as h}from"./notifications-DM-9a7Is.js";/**
 * @license @tabler/icons-react v3.1.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var v=u("outline","globe","IconGlobe",[["path",{d:"M7 9a4 4 0 1 0 8 0a4 4 0 0 0 -8 0",key:"svg-0"}],["path",{d:"M5.75 15a8.015 8.015 0 1 0 9.25 -13",key:"svg-1"}],["path",{d:"M11 17v4",key:"svg-2"}],["path",{d:"M7 21h8",key:"svg-3"}]]);/**
 * @license @tabler/icons-react v3.1.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var g=u("outline","note","IconNote",[["path",{d:"M13 20l7 -7",key:"svg-0"}],["path",{d:"M13 20v-6a1 1 0 0 1 1 -1h6v-7a2 2 0 0 0 -2 -2h-12a2 2 0 0 0 -2 2v12a2 2 0 0 0 2 2h7",key:"svg-1"}]]);function y({partPk:a,supplierPk:n,hidePart:c}){const[r,s]=t.useState(a);return t.useEffect(()=>{s(a)},[a]),t.useMemo(()=>{const o={part:{hidden:c,value:r,onValueChange:s,filters:{purchaseable:!0}},manufacturer_part:{filters:{part_detail:!0,manufacturer_detail:!0},adjustFilters:i=>(r&&(i.part=r),i)},supplier:{},SKU:{icon:e.jsx(m,{})},description:{},link:{icon:e.jsx(h,{})},note:{icon:e.jsx(g,{})},pack_quantity:{},packaging:{icon:e.jsx(f,{})}};return n!==void 0&&(o.supplier.value=n),o},[r])}function _(){return t.useMemo(()=>({part:{},manufacturer:{},MPN:{},description:{},link:{}}),[])}function b(){return t.useMemo(()=>({name:{},value:{},units:{}}),[])}function F(){return{name:{},description:{},website:{icon:e.jsx(v,{})},currency:{icon:e.jsx(l,{})},phone:{icon:e.jsx(p,{})},email:{icon:e.jsx(d,{})},is_supplier:{},is_manufacturer:{},is_customer:{}}}export{y as a,b,F as c,_ as u};
