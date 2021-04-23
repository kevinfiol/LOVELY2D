const json = require('./output.json');

const typeFuncs = {}
const firstLevel = {};
const secondLevel = {};
for (let key in json) {
    if (key.split(':').length == 2) {
        typeFuncs[key] = json[key];
        delete json[key];
        continue;
    }

    if (key.split('.').length == 2) {
        firstLevel[key] = json[key];
        delete json[key];
    }

    if (key.split('.').length == 3) {
        secondLevel[key] = json[key];
        delete json[key];
    }
}

const reordered = {
    ...firstLevel,
    ...secondLevel,
    ...typeFuncs
};

require('fs').writeFileSync('./output.json', JSON.stringify(reordered));