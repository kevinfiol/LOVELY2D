local api = require 'love_api'
local json = require 'json'
local inspect = require 'inspect'

function string:split(delimiter)
    local result = {}
    local from = 1
    local delim_from, delim_to = string.find(self, delimiter, from, true)
    while delim_from do
        if (delim_from ~= 1) then
            table.insert(result, string.sub(self, from, delim_from-1))
        end
        from = delim_to + 1
        delim_from, delim_to = string.find(self, delimiter, from, true)
    end
    if (from <= #self) then table.insert(result, string.sub(self, from)) end
    return result
end

function makeWikiLink(endpoint)
    return 'https://love2d.org/wiki/' .. endpoint
end

function makeApiLink(endpoint)
    return 'https://love2d-community.github.io/love-api/#' .. endpoint
end

function exists(x)
    return x ~= nil
end

function ternary(cond, T, F)
    if cond then return T else return F end
end

function parseFunctions(t, parent, namespace, isTypeFuncs)
    if isTypeFuncs == nil then isTypeFuncs = false end
    for _, fn in ipairs(t) do
        local name = namespace .. '.' .. fn.name

        -- string manip stuff for links
        -- possible namespaces
        -- love.module.Type
        -- love.module
        -- love.Type

        local tokens = namespace:split('.')
        local wikiLink = nil
        local apiLink = nil

        if isTypeFuncs then
            local typeName = nil
            if #tokens == 3 then typeName = tokens[3] end
            if #tokens == 2 then typeName = tokens[2] end
            wikiLink = makeWikiLink(typeName .. ':' .. fn.name)
            apiLink = makeApiLink(typeName .. '_' .. fn.name)
        else
            if #tokens == 2 then
                local moduleName = tokens[2]
                wikiLink = makeWikiLink('love.' .. moduleName .. '.' .. fn.name)
                apiLink = makeApiLink(moduleName .. '_' .. fn.name)
            else
                wikiLink = makeWikiLink('love.' .. fn.name)
                apiLink = makeApiLink(fn.name)
            end
        end

        parent[name] = {
            meta = {
                prop_type = 'function',
                is_type_func = isTypeFuncs,
                name = fn.name,
                namespace = namespace,
                description = fn.description,
                api_link = apiLink,
                wiki_link = wikiLink,
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
            local wikiLink = makeWikiLink(ty.name)
            local apiLink = makeApiLink('type_' .. ty.name)

            parent[name] = {
                meta = {
                    prop_type = 'type',
                    name = ty.name,
                    namespace = namespace,
                    description = ty.description,
                    api_link = apiLink,
                    wiki_link = wikiLink,
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
                parseFunctions(ty.functions, parent, name, true)
            end
        end
    end
end

function parseModules(t, parent, namespace)
    for _, mod in ipairs(t) do
        if exists(mod.name) then
            local name = namespace .. '.' .. mod.name
            local wikiLink = makeWikiLink('love.' .. mod.name)
            local apiLink = makeApiLink(mod.name)

            parent[name] = {
                meta = {
                    prop_type = 'module',
                    name = mod.name,
                    namespace = namespace,
                    description = mod.description,
                    api_link = apiLink,
                    wiki_link = wikiLink
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

api_json = json.encode(love)
local file = io.open('output.json', 'w')
file:write(api_json)
file:close()