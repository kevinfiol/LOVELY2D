const json = require('./output.json');

const firstLevel = {};
const secondLevel = {};
const thirdLevel = {}
for (let key in json) {
    if (key.split('.').length == 2) {
        firstLevel[key] = json[key];
        delete json[key];
    }

    if (key.split('.').length == 3) {
        secondLevel[key] = json[key];
        delete json[key];
    }

    if (key.split('.').length == 4) {
        thirdLevel[key] = json[key];
        delete json[key];
    }
}

const reordered = {
    ...firstLevel,
    ...secondLevel,
    ...thirdLevel
};

require('fs').writeFileSync('./output.json', JSON.stringify(reordered));