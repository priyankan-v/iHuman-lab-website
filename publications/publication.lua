local bibfile = "publications.bib"
local my_name = "Manjunatha, Hemanth"

-- Simple BibTeX parser
function parse_bib(filename)
  local entries = {}
  local current = nil

  for line in io.lines(filename) do
    if line:match("^@") then
      current = {}
    elseif current then
      local key, value = line:match("%s*(%w+)%s*=%s*{(.+)}")
      if key and value then
        current[key:lower()] = value:gsub("},?$", "")
      end
    end

    if line:match("^}$") and current then
      table.insert(entries, current)
      current = nil
    end
  end

  return entries
end

-- Format authors: bold your name
local function format_authors(author_text)
  local parts = {}
  local authors = {}

  -- Split by "and" keyword
  for auth in author_text:gmatch("([^,]+,[^,]+)") do
    auth = auth:gsub("^%s+", ""):gsub("%s+$", "") -- trim
    table.insert(authors, auth)
  end

  for i, auth in ipairs(authors) do
    if auth == my_name then
      table.insert(parts, pandoc.Strong({pandoc.Str(auth)}))
    else
      table.insert(parts, pandoc.Str(auth))
    end
    -- Add a space **only if not last author**
    if i < #authors then
      table.insert(parts, pandoc.Str(" "))
    end
  end

  return parts
end


-- Build citation inlines
local function build_citation(e)
  local inlines = {}

  -- Authors
  if e.author then
    local authors_formatted = format_authors(e.author)
    for _, a in ipairs(authors_formatted) do table.insert(inlines, a) end
    table.insert(inlines, pandoc.Str(". "))
  end

  -- Title
  if e.title then
    table.insert(inlines, pandoc.Strong({pandoc.Str(e.title .. ". ")}))
  end

  -- Journal or Conference
    local type_label = ""
    if e.journal then
    -- Check if it's arXiv
    if e.journal:lower():match("arxiv") then
        type_label = "arXiv"
    else
        type_label = "Journal"
    end
    elseif e.booktitle then
    type_label = "Conference"
    end

  -- Volume, number, pages, publisher
  if e.volume then table.insert(inlines, pandoc.Str("Vol. " .. e.volume .. ". ")) end
  if e.number then table.insert(inlines, pandoc.Str("No. " .. e.number .. ". ")) end
  if e.pages then table.insert(inlines, pandoc.Str("pp. " .. e.pages .. ". ")) end
  if e.publisher then table.insert(inlines, pandoc.Str(e.publisher .. ". ")) end

  return inlines, type_label
end

local function make_id(str)
  str = str:lower()
  str = str:gsub("%s+", "-")      -- spaces → dash
  str = str:gsub("[^%w%-]", "")   -- remove non-alphanum/dash
  return str
end

-- Main Pandoc filter
function Pandoc(doc)
  local entries = parse_bib(bibfile)
  local grouped = {}

  -- Group by year
  for _, e in ipairs(entries) do
    local year = e.year or "Misc"
    if not grouped[year] then grouped[year] = {} end
    table.insert(grouped[year], e)
  end

  -- Sort years descending
  local years = {}
  for y in pairs(grouped) do table.insert(years, y) end
  table.sort(years, function(a, b)
  local na = tonumber(a)
  local nb = tonumber(b)

  if na and nb then
    return na > nb            -- numeric years descending
  elseif na then
    return true               -- numeric year before non-numeric
  elseif nb then
    return false              -- numeric year before non-numeric
  else
    return a < b              -- both non-numeric, sort alphabetically
  end
end)

  local blocks = {}

  for _, year in ipairs(years) do
     local header_id = make_id(year)
  table.insert(blocks, pandoc.Header(2, pandoc.Str(year), {id = header_id}))

    for _, e in ipairs(grouped[year]) do
      local citation_inlines, type_label = build_citation(e)

      -- Badge
      local badge_span = pandoc.Span({pandoc.Str(type_label)}, {class = "publication-badge"})

      -- Combine badge and citation
      table.insert(citation_inlines, pandoc.Space())
      table.insert(citation_inlines, badge_span)

      -- Wrap in a card div
      local card_div = pandoc.Div(
        { pandoc.Para(citation_inlines) },
        { class = "publication-card" }
      )

      table.insert(blocks, card_div)
    end
  end

  doc.blocks = blocks
  return doc
end
