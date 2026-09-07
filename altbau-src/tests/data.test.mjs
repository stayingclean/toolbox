import {test} from 'node:test';
import assert from 'node:assert/strict';
import {propertyTree} from '../properties.mjs';
import {validateView,validateMeasurements} from '../files.mjs';
test('IFC property graphs retain values without cycling through the element again',()=>{
 const element={Name:{value:'Wall'},IsDefinedBy:[]},pset={Name:{value:'Pset'},HasProperties:[{Name:{value:'Height'},NominalValue:{value:2.8}}],DefinesOccurrence:[element]};element.IsDefinedBy.push(pset);
 const tree=propertyTree(element);assert.equal(tree.IsDefinedBy[0].HasProperties[0].NominalValue,2.8);assert.doesNotThrow(()=>JSON.stringify(tree));
});
test('malformed measurement imports are rejected before user data is replaced',()=>{
 assert.throws(()=>validateMeasurements({format:'altbau-measurements',version:1,measurements:[{type:'length',points:[[0,0,0],[0,0,0]]}]}));
 assert.throws(()=>validateMeasurements({format:'altbau-measurements',version:1,measurements:[{type:'length',points:[[0,0,0],[Infinity,0,0]]}]}));
 assert.throws(()=>validateMeasurements({format:'other',version:1,measurements:[]}));
});
test('views from another model or invalid clipping planes are rejected',()=>{
 const valid={format:'altbau-view',version:1,projection:'Perspective',position:[1,2,3],target:[0,0,0],visible:['wall'],planes:[{normal:[1,0,0],origin:[0,0,0]}]};
 assert.equal(validateView(valid,new Set(['wall'])),valid);
 for(const zoom of [0,-1,Infinity,1001,'2'])assert.throws(()=>validateView({...valid,zoom},new Set(['wall'])));
 assert.throws(()=>validateView({...valid,visible:['unknown']},new Set(['wall'])));
 assert.throws(()=>validateView({...valid,planes:[{normal:[0,0,0],origin:[0,0,0]}]},new Set(['wall'])));
});
