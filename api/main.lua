local api = require 'love_api'
local json = require 'json'
local inspect = require 'inspect'

function exists(x)
    return x ~= nil
end

function ternary(cond, T, F)
    if cond then return T else return F end
end

function parseFunctions(t, parent, namespace)
    for _, fn in ipairs(t) do
        local name = namespace .. '.' .. fn.name
        parent[name] = {
            meta = {
                prop_type = 'function',
                name = fn.name,
                description = fn.description,
                returns = ternary(exists(fn.variants[1].returns), fn.variants[1].returns, nil),
                arguments = ternary(exists(fn.variants[1].arguments), fn.variants[1].arguments, nil)
            }
        }
    end
end

function parseTypes(t, parent, namespace)
    for _, ty in ipairs(t) do
        if exists(ty.name) then
            local name = namespace .. '.' .. ty.name
            parent[name] = {
                meta = {
                    prop_type = 'type',
                    name = ty.name,
                    description = ty.description,
                    constructors = ternary(exists(ty.constructors), ty.constructors, nil),
                    supertypes = ternary(ty.supertypes, ty.supertypes, nil)
                }
            }

            -- parent[name].functions = ternary(
            --     exists(ty.functions),
            --     parseFunctions(ty.functions, parent[name], name),
            --     nil
            -- )
            if ty.functions ~= nil then
                parseFunctions(ty.functions, parent, name)
            end
        end
    end
end

function parseModules(t, parent, namespace)
    for _, mod in ipairs(t) do
        if exists(mod.name) then
            local name = namespace .. '.' .. mod.name
            parent[name] = {
                meta = {
                    prop_type = 'module',
                    name = mod.name,
                    description = mod.description
                }
            }

            parseFunctions(mod.functions, parent, name)
            parseTypes(mod.types, parent, name)
        end
    end
end

local love = {}

parseFunctions(api.functions, love, 'love')
parseModules(api.modules, love, 'love')
parseFunctions(api.callbacks, love, 'love')
parseTypes(api.types, love, 'love')

local file = io.open('output.json', 'w')
file:write(json.encode(love))
file:close()