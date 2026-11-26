-- Universal mGBA Soul Link Bridge: Gen 1 (R/B/Y) + Gen 2 (G/S/C) + Gen 3 (R/S/E/FR/LG)
local HOST = "127.0.0.1"
local PORT = 55355
local PLAYER_ID = 1

local sock = nil
local connected = false
local frame_counter = 0
local clear_enemy_recharge = false
local DETECTED_GEN = nil

-- true: Gen 3 battle_type is 1 = wild, 2 = trainer (same meaning as Gen 1/2).
-- false: legacy behaviour (reported 2 almost all the time on Gen 3).
local GEN3_STRICT_TRAINER_FLAG = true

local logged_once = {}
local function log_once(msg)
    if not logged_once[msg] then
        logged_once[msg] = true
        console:log("[SoulLink] " .. msg)
    end
end

local GEN3_P, GEN3_VERIFIED = nil, false

local GEN1_TO_DEX = {
    [0x01]=112,[0x02]=115,[0x03]=32,[0x04]=35,[0x05]=21,[0x06]=100,[0x07]=34,[0x08]=80,
    [0x09]=2,[0x0A]=103,[0x0B]=108,[0x0C]=102,[0x0D]=88,[0x0E]=94,[0x0F]=29,[0x10]=31,
    [0x11]=104,[0x12]=111,[0x13]=131,[0x14]=59,[0x15]=151,[0x16]=130,[0x17]=90,[0x18]=72,
    [0x19]=92,[0x1A]=123,[0x1B]=120,[0x1C]=9,[0x1D]=127,[0x1E]=114,[0x21]=58,[0x22]=95,
    [0x23]=22,[0x24]=16,[0x25]=79,[0x26]=64,[0x27]=75,[0x28]=113,[0x29]=67,[0x2A]=122,
    [0x2B]=106,[0x2C]=107,[0x2D]=24,[0x2E]=47,[0x2F]=54,[0x30]=96,[0x31]=76,[0x33]=126,
    [0x35]=125,[0x36]=82,[0x37]=109,[0x39]=56,[0x3A]=86,[0x3B]=50,[0x3C]=128,[0x40]=83,
    [0x41]=48,[0x42]=149,[0x46]=84,[0x47]=60,[0x48]=124,[0x49]=146,[0x4A]=144,[0x4B]=145,
    [0x4C]=132,[0x4D]=52,[0x4E]=98,[0x52]=37,[0x53]=38,[0x54]=25,[0x55]=26,[0x58]=147,
    [0x59]=148,[0x5A]=140,[0x5B]=141,[0x5C]=116,[0x5D]=117,[0x60]=27,[0x61]=28,[0x62]=138,
    [0x63]=139,[0x64]=39,[0x65]=40,[0x66]=133,[0x67]=136,[0x68]=135,[0x69]=134,[0x6A]=66,
    [0x6B]=41,[0x6C]=23,[0x6D]=46,[0x6E]=61,[0x6F]=62,[0x70]=13,[0x71]=14,[0x72]=15,
    [0x74]=85,[0x75]=57,[0x76]=51,[0x77]=49,[0x78]=87,[0x7B]=10,[0x7C]=11,[0x7D]=12,
    [0x7E]=68,[0x80]=55,[0x81]=97,[0x82]=42,[0x83]=150,[0x84]=143,[0x85]=129,[0x88]=89,
    [0x8A]=99,[0x8B]=91,[0x8D]=101,[0x8E]=36,[0x8F]=110,[0x90]=53,[0x91]=105,[0x93]=93,
    [0x94]=63,[0x95]=65,[0x96]=17,[0x97]=18,[0x98]=121,[0x99]=1,[0x9A]=3,[0x9B]=73,
    [0x9D]=118,[0x9E]=119,[0xA3]=77,[0xA4]=78,[0xA5]=19,[0xA6]=20,[0xA7]=33,[0xA8]=30,
    [0xA9]=74,[0xAA]=137,[0xAB]=142,[0xAD]=81,[0xB0]=4,[0xB1]=7,[0xB2]=5,[0xB3]=8,
    [0xB4]=6,[0xB9]=43,[0xBA]=44,[0xBB]=45,[0xBC]=69,[0xBD]=70,[0xBE]=71
}

local GB_TYPE_NORM = {
    [0x00]=0,[0x01]=1,[0x02]=2,[0x03]=3,[0x04]=4,[0x05]=5,[0x07]=6,[0x08]=7,[0x09]=8,
    [0x14]=9,[0x15]=10,[0x16]=11,[0x17]=12,[0x18]=13,[0x19]=14,[0x1A]=15,[0x1B]=16
}

local GB_CHAR_MAP = {
    [0x80]="A",[0x81]="B",[0x82]="C",[0x83]="D",[0x84]="E",[0x85]="F",[0x86]="G",[0x87]="H",
    [0x88]="I",[0x89]="J",[0x8A]="K",[0x8B]="L",[0x8C]="M",[0x8D]="N",[0x8E]="O",[0x8F]="P",
    [0x90]="Q",[0x91]="R",[0x92]="S",[0x93]="T",[0x94]="U",[0x95]="V",[0x96]="W",[0x97]="X",
    [0x98]="Y",[0x99]="Z",[0xA0]="a",[0xA1]="b",[0xA2]="c",[0xA3]="d",[0xA4]="e",[0xA5]="f",
    [0xA6]="g",[0xA7]="h",[0xA8]="i",[0xA9]="j",[0xAA]="k",[0xAB]="l",[0xAC]="m",[0xAD]="n",
    [0xAE]="o",[0xAF]="p",[0xB0]="q",[0xB1]="r",[0xB2]="s",[0xB3]="t",[0xB4]="u",[0xB5]="v",
    [0xB6]="w",[0xB7]="x",[0xB8]="y",[0xB9]="z",[0x7F]=" ",[0xE3]="-",[0xE7]="!",[0xE6]="?",
    [0xE0]="'",[0xE8]=".",[0xF3]="/",[0xF4]=",",[0xEF]="♂",[0xF5]="♀",
    [0xF6]="0",[0xF7]="1",[0xF8]="2",[0xF9]="3",[0xFA]="4",
    [0xFB]="5",[0xFC]="6",[0xFD]="7",[0xFE]="8",[0xFF]="9"
}

local GBA_CHAR_MAP = {
    [0x00]=" ",[0xBB]="A",[0xBC]="B",[0xBD]="C",[0xBE]="D",[0xBF]="E",[0xC0]="F",[0xC1]="G",
    [0xC2]="H",[0xC3]="I",[0xC4]="J",[0xC5]="K",[0xC6]="L",[0xC7]="M",[0xC8]="N",[0xC9]="O",
    [0xCA]="P",[0xCB]="Q",[0xCC]="R",[0xCD]="S",[0xCE]="T",[0xCF]="U",[0xD0]="V",[0xD1]="W",
    [0xD2]="X",[0xD3]="Y",[0xD4]="Z",[0xD5]="a",[0xD6]="b",[0xD7]="c",[0xD8]="d",[0xD9]="e",
    [0xDA]="f",[0xDB]="g",[0xDC]="h",[0xDD]="i",[0xDE]="j",[0xDF]="k",[0xE0]="l",[0xE1]="m",
    [0xE2]="n",[0xE3]="o",[0xE4]="p",[0xE5]="q",[0xE6]="r",[0xE7]="s",[0xE8]="t",[0xE9]="u",
    [0xEA]="v",[0xEB]="w",[0xEC]="x",[0xED]="y",[0xEE]="z",[0xAE]="-",[0xAB]="!",[0xAC]="?"
}

local GEN3_GROWTH_STR = "000000112323112323112323"

local GEN3_HOENN_LIST = {
    252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,
    270,271,272,273,274,275,290,291,292,276,277,285,286,327,278,279,283,284,
    320,321,300,301,352,343,344,299,324,302,339,340,370,341,342,349,350,318,
    319,328,329,330,296,297,309,310,322,323,363,364,365,331,332,361,362,337,
    338,298,325,326,311,312,303,307,308,333,334,360,355,356,315,287,288,289,
    316,317,357,293,294,295,366,367,368,359,353,354,336,335,369,304,305,306,
    351,313,314,345,346,347,348,280,281,282,371,372,373,374,375,376,377,378,
    379,382,383,384,380,381,385,386,358
}

local function read16_be(addr)
    return (emu:read8(addr) * 256) + emu:read8(addr + 1)
end

local function write16_be(addr, val)
    emu:write8(addr, math.floor(val / 256) % 256)
    emu:write8(addr + 1, val % 256)
end

local function read16_le(addr)
    return emu:read8(addr) + (emu:read8(addr + 1) * 256)
end

local function write16_le(addr, val)
    emu:write8(addr, val % 256)
    emu:write8(addr + 1, math.floor(val / 256) % 256)
end

local function read32_le(addr)
    return emu:read8(addr)
        + (emu:read8(addr + 1) * 256)
        + (emu:read8(addr + 2) * 65536)
        + (emu:read8(addr + 3) * 16777216)
end

local bxor32 = (function()
    local mk = load and load("return function(a, b) return (a ~ b) & 0xFFFFFFFF end")
    if mk then
        local ok, fn = pcall(mk)
        if ok and type(fn) == "function" then return fn end
    end
    return function(a, b)
        local res, bitval = 0, 1
        for _ = 1, 32 do
            if (a % 2) ~= (b % 2) then res = res + bitval end
            a = math.floor(a / 2)
            b = math.floor(b / 2)
            bitval = bitval * 2
        end
        return res
    end
end)()

local function detect_game()
    if DETECTED_GEN then return DETECTED_GEN end
    local ok_gba, code = pcall(function()
        local c = ""
        for i = 0, 3 do c = c .. string.char(emu:read8(0x080000AC + i)) end
        return c
    end)
    local fam = nil
    if ok_gba and code then
        local p3 = string.sub(code, 1, 3)
        if p3 == "AXV" or p3 == "AXP" then fam = "RS"          -- Ruby / Sapphire
        elseif p3 == "BPR" or p3 == "BPG" then fam = "FRLG"    -- FireRed / LeafGreen
        elseif p3 == "BPE" then fam = "E" end                  -- Emerald
    end
    if fam then
        local rev = emu:read8(0x080000BC)
        DETECTED_GEN = { gen = 3, code = code, sub = (fam == "FRLG") and "FRLG" or "RSE", family = fam, rev = rev }
        console:log(string.format("[SoulLink] Detected Gen 3 GBA ROM: %s (v1.%d)", code, rev))
        if string.sub(code, 4, 4) ~= "E" then
            console:log("[SoulLink] WARNING: non-English ROM - memory addresses are for English versions.")
        end
        return DETECTED_GEN
    end

    local title = ""
    for i = 0, 14 do
        local b = emu:read8(0x0134 + i)
        if b >= 32 and b <= 126 then title = title .. string.char(b) end
    end
    if string.find(title, "CRYSTAL") then
        DETECTED_GEN = { gen = 2, sub = "CRYSTAL" }
    elseif string.find(title, "GLD") or string.find(title, "SLV")
        or string.find(title, "GOLD") or string.find(title, "SILVER") then
        DETECTED_GEN = { gen = 2, sub = "GS" }
    else
        DETECTED_GEN = { gen = 1, sub = "RBY" }
    end
    console:log("[SoulLink] Detected Gen " .. tostring(DETECTED_GEN.gen) .. " ROM (" .. title .. ")")
    return DETECTED_GEN
end

local function read_gb_nick(base, slot_idx, stride)
    local addr = base + (slot_idx * stride)
    local chars = {}
    for i = 0, 9 do
        local b = emu:read8(addr + i)
        if b == 0x50 then break end
        table.insert(chars, GB_CHAR_MAP[b] or "?")
    end
    return table.concat(chars)
end

local function gba_species_to_dex(raw_sp)
    if raw_sp <= 251 then return raw_sp end
    return GEN3_HOENN_LIST[raw_sp - 276] or raw_sp
end

-- ---------------------------------------------------------------------------
-- Gen 3 memory profiles (English ROMs). RS = Ruby/Sapphire, FRLG, E = Emerald.
-- The same addresses are used for every revision (v1.0/1.1/1.2); the script
-- verifies them at runtime by checking each party Pokemon's checksum.
-- ---------------------------------------------------------------------------
local GEN3_PROFILES = {
    RS = {{
        name = "Ruby/Sapphire",
        pc = 0x03004350, pp = 0x03004360, ep = 0x030045C0,
        sb1 = 0x02025734, sb1_is_ptr = false, hdr = 0x0202E828,
        bm = {0x02024A80}, flags = 0x020239F8, sel = 0x02024E60,
        ball_off = 0x600, ball_n = 16,
    }},
    FRLG = {{
        name = "FireRed/LeafGreen",
        pc = 0x02024029, pp = 0x02024284, ep = 0x0202402C,
        sb1 = 0x03005008, sb1_is_ptr = true,
        bm = {0x02023BE4, 0x02023BE8}, flags = 0x02022B4C, sel = 0x02023FF8,
        ball_off = 0x430, ball_n = 13,
    }},
    E = {{
        name = "Emerald",
        pc = 0x020244E9, pp = 0x020244EC, ep = 0x02024744,
        sb1 = 0x03005D8C, sb1_is_ptr = true,
        bm = {0x02024084}, flags = 0x02022FEC, sel = 0x02024498,
        ball_off = 0x650, ball_n = 16,
    }},
}

local function gen3_checksum_ok(base)
    local pid  = read32_le(base)
    local otid = read32_le(base + 4)
    if pid == 0 and otid == 0 then return false end
    local key = bxor32(pid, otid)
    local sum = 0
    for i = 0, 11 do
        local w = bxor32(read32_le(base + 0x20 + i * 4), key)
        sum = sum + (w % 65536) + math.floor(w / 65536)
    end
    return (sum % 65536) == read16_le(base + 0x1C)
end

-- true = profile matches this ROM, false = does not, nil = can't tell (empty party)
local function gen3_profile_state(p)
    local count = emu:read8(p.pc)
    if count == 0 then return nil end
    if count > 6 then return false end
    for i = 0, count - 1 do
        if not gen3_checksum_ok(p.pp + i * 100) then return false end
    end
    return true
end

local function get_gen3()
    if GEN3_P and GEN3_VERIFIED then return GEN3_P end
    local g = detect_game()
    local list = g and GEN3_PROFILES[g.family]
    if not list then return nil end
    local unknown = nil
    for _, p in ipairs(list) do
        local st = gen3_profile_state(p)
        if st == true then
            GEN3_P, GEN3_VERIFIED = p, true
            console:log("[SoulLink] Verified Gen 3 memory layout: " .. p.name)
            return p
        elseif st == nil and not unknown then
            unknown = p
        end
    end
    GEN3_P = GEN3_P or unknown or list[1]
    if not unknown then
        log_once("WARNING: party data at the expected " .. list[1].name ..
            " addresses failed its checksum. This ROM revision/language may use different addresses.")
    end
    return GEN3_P
end

local function battle_slot_matches(a, pid)
    if read32_le(a + 0x48) ~= pid then return false end
    local lvl = emu:read8(a + 0x2A)
    local hp  = read16_le(a + 0x28)
    local mhp = read16_le(a + 0x2C)
    return lvl >= 1 and lvl <= 100 and mhp > 0 and hp <= mhp
end

-- Finds the BattlePokemon struct (gBattleMons[0] or [2]) of one of our own mons.
-- Tries the known gBattleMons address first, then scans EWRAM for the personality value.
local function find_player_battle_slot(gp, pid)
    -- returns: address, battler index (0 = left, 2 = right), gBattleMons base
    for _, base in ipairs(gp.bm) do
        for n, off in ipairs({0x00, 0xB0}) do
            if battle_slot_matches(base + off, pid) then return base + off, (n - 1) * 2, base end
        end
    end
    for a = 0x02022000, 0x02026000 - 0x58, 4 do
        if battle_slot_matches(a, pid) then
            log_once(string.format("Battle struct found by scan at 0x%08X", a))
            return a, nil, nil
        end
    end
    return nil
end

-- ---------------------------------------------------------------------------
-- Route names
-- ---------------------------------------------------------------------------
local HOENN_MAPSEC_SPECIAL = {
    [50]="Underwater Route 124",[51]="Underwater Route 126",[52]="Underwater Route 127",
    [53]="Underwater Route 128",[54]="Underwater Sootopolis City",[55]="Granite Cave",
    [56]="Mt. Chimney",[57]="Safari Zone",[58]="Battle Tower",[59]="Petalburg Woods",
    [60]="Rusturf Tunnel",[61]="Abandoned Ship",[62]="New Mauville",[63]="Meteor Falls",
    [64]="Meteor Falls",[65]="Mt. Pyre",[66]="Hideout",[67]="Shoal Cave",[68]="Seafloor Cavern",
    [69]="Underwater Seafloor Cavern",[70]="Victory Road",[71]="Mirage Island",[72]="Cave of Origin",
    [73]="Southern Island",[74]="Fiery Path",[75]="Fiery Path",[76]="Jagged Pass",[77]="Jagged Pass",
    [78]="Sealed Chamber",[79]="Scorched Slab",[80]="Island Cave",[81]="Desert Ruins",
    [82]="Ancient Tomb",[83]="Inside of Truck",[84]="Sky Pillar",
}
local HOENN_MAPSEC_TOWNS = {
    [0]="Littleroot Town",[1]="Oldale Town",[2]="Dewford Town",[3]="Lavaridge Town",
    [4]="Fallarbor Town",[5]="Verdanturf Town",[6]="Pacifidlog Town",[7]="Petalburg City",
    [8]="Slateport City",[9]="Mauville City",[10]="Rustboro City",[11]="Fortree City",
    [12]="Lilycove City",[13]="Mossdeep City",[14]="Sootopolis City",[15]="Ever Grande City",
}
local HOENN_GROUP0_TOWNS = {
    [0]="Petalburg City",[1]="Slateport City",[2]="Mauville City",[3]="Rustboro City",
    [4]="Fortree City",[5]="Lilycove City",[6]="Mossdeep City",[7]="Sootopolis City",
    [8]="Ever Grande City",[9]="Littleroot Town",[10]="Oldale Town",[11]="Dewford Town",
    [12]="Lavaridge Town",[13]="Fallarbor Town",[14]="Verdanturf Town",[15]="Pacifidlog Town",
}

local FRLG_GROUP3 = {
    [0x00]="Pallet Town",[0x01]="Viridian City",[0x02]="Pewter City",[0x03]="Cerulean City",
    [0x04]="Lavender Town",[0x05]="Vermilion City",[0x06]="Celadon City",[0x07]="Fuchsia City",
    [0x08]="Cinnabar Island",[0x09]="Indigo Plateau",[0x0A]="Saffron City",[0x0B]="Saffron City",
    [0x0C]="One Island",[0x0D]="Two Island",[0x0E]="Three Island",[0x0F]="Four Island",
    [0x10]="Five Island",[0x11]="Seven Island",[0x12]="Six Island",
    [0x27]="Route 21",[0x28]="Route 21",[0x29]="Route 22",[0x2A]="Route 23",[0x2B]="Route 24",
    [0x2C]="Route 25",[0x2D]="Kindle Road",[0x2E]="Treasure Beach",[0x2F]="Cape Brink",
    [0x30]="Bond Bridge",[0x31]="Three Island Port",[0x36]="Resort Gorgeous",[0x37]="Water Labyrinth",
    [0x38]="Five Island Meadow",[0x39]="Memorial Pillar",[0x3A]="Outcast Island",[0x3B]="Green Path",
    [0x3C]="Water Path",[0x3D]="Ruin Valley",[0x3E]="Trainer Tower",[0x3F]="Canyon Entrance",
    [0x40]="Sevault Canyon",[0x41]="Tanoby Ruins",
}
-- map groups 4..42 are building interiors; attribute them to the town/route they belong to
local FRLG_INTERIOR_PARENT = {
    [4]="Pallet Town",[5]="Viridian City",[6]="Pewter City",[7]="Cerulean City",[8]="Lavender Town",
    [9]="Vermilion City",[10]="Celadon City",[11]="Fuchsia City",[12]="Cinnabar Island",
    [13]="Indigo Plateau",[14]="Saffron City",[15]="Route 2",[16]="Route 4",[17]="Route 5",
    [18]="Route 6",[19]="Route 7",[20]="Route 8",[21]="Route 10",[22]="Route 11",[23]="Route 12",
    [24]="Route 15",[25]="Route 16",[26]="Route 18",[27]="Route 19",[28]="Route 22",[29]="Route 23",
    [30]="Route 25",[31]="Seven Island",[32]="One Island",[33]="Two Island",[34]="Three Island",
    [35]="Four Island",[36]="Five Island",[37]="Six Island",[38]="Three Island",[39]="Five Island",
    [40]="Two Island",[41]="Six Island",[42]="Seven Island",
}

local function frlg_route_name(group, num)
    if group == 3 then
        if num >= 0x13 and num <= 0x26 then return "Route " .. tostring(num - 0x12) end
        if FRLG_GROUP3[num] then return FRLG_GROUP3[num] end
    elseif group == 1 then
        if num == 0x00 then return "Viridian Forest" end
        if num <= 0x03 then return "Mt. Moon" end
        if num <= 0x1D then return "S.S. Anne" end
        if num <= 0x23 then return "Underground Path" end
        if num <= 0x26 then return "Diglett's Cave" end
        if num <= 0x29 then return "Victory Road" end
        if num <= 0x2E then return "Rocket Hideout" end
        if num <= 0x3A then return "Silph Co." end
        if num <= 0x3E then return "Pokemon Mansion" end
        if num <= 0x47 then return "Safari Zone" end
        if num <= 0x4A then return "Cerulean Cave" end
        if num <= 0x50 then return "Pokemon League" end
        if num <= 0x52 then return "Rock Tunnel" end
        if num <= 0x57 then return "Seafoam Islands" end
        if num <= 0x5E then return "Pokemon Tower" end
        if num == 0x5F then return "Power Plant" end
        if num <= 0x6C then return "Mt. Ember" end
        if num == 0x6D then return "Berry Forest" end
        if num <= 0x71 then return "Icefall Cave" end
        if num == 0x72 then return "Rocket Warehouse" end
        if num <= 0x78 then return "Dotted Hole" end
        if num == 0x79 then return "Pattern Bush" end
        if num == 0x7A then return "Altering Cave" end
    elseif group == 2 then
        if num == 0x00 then return "Navel Rock" end
        if num <= 0x0B then return "Trainer Tower" end
        if num <= 0x1A then return "Lost Cave" end
        if num <= 0x21 then return "Tanoby Ruins" end
        if num == 0x22 then return "Dunsparce Tunnel" end
        if num == 0x23 then return "Sevault Canyon" end
        if num <= 0x37 then return "Navel Rock" end
        if num == 0x38 or num == 0x3A then return "Birth Island" end
        if num == 0x39 then return "Kindle Road" end
        if num == 0x3B then return "Navel Rock" end
    elseif group == 0 then
        return "Link Room"
    elseif FRLG_INTERIOR_PARENT[group] then
        return FRLG_INTERIOR_PARENT[group]
    end
    return string.format("Map %d-%d", group, num)
end

local function hoenn_route_name(group, num, mapsec)
    if group == 0 then
        if num >= 16 and num <= 49 then return "Route " .. tostring(num + 85) end
        if HOENN_GROUP0_TOWNS[num] then return HOENN_GROUP0_TOWNS[num] end
    end
    if mapsec ~= nil then
        if mapsec >= 16 and mapsec <= 49 then return "Route " .. tostring(mapsec + 85) end
        if HOENN_MAPSEC_TOWNS[mapsec] then return HOENN_MAPSEC_TOWNS[mapsec] end
        if HOENN_MAPSEC_SPECIAL[mapsec] then return HOENN_MAPSEC_SPECIAL[mapsec] end
    end
    if group == 0 then
        if num >= 16 and num <= 49 then return "Route " .. tostring(num + 85) end
        if HOENN_GROUP0_TOWNS[num] then return HOENN_GROUP0_TOWNS[num] end
    end
    return string.format("Map %d-%d", group, num)
end

local GEN1_MAP_NAMES = {
    [0]="Pallet Town", [1]="Viridian City", [2]="Pewter City", [3]="Cerulean City", [4]="Lavender Town",
    [5]="Vermilion City", [6]="Celadon City", [7]="Fuchsia City", [8]="Cinnabar Island", [9]="Indigo Plateau",
    [10]="Saffron City", [12]="Route 1", [13]="Route 2", [14]="Route 3", [15]="Route 4", [16]="Route 5",
    [17]="Route 6", [18]="Route 7", [19]="Route 8", [20]="Route 9", [21]="Route 10", [22]="Route 11",
    [23]="Route 12", [24]="Route 13", [25]="Route 14", [26]="Route 15", [27]="Route 16", [28]="Route 17",
    [29]="Route 18", [30]="Route 19", [31]="Route 20", [32]="Route 21", [33]="Route 22", [34]="Route 23",
    [35]="Route 24", [36]="Route 25", [37]="Pallet Town", [38]="Pallet Town", [39]="Pallet Town",
    [40]="Pallet Town", [41]="Viridian City", [42]="Viridian City", [43]="Viridian City", [44]="Viridian City",
    [45]="Viridian City", [46]="Diglett's Cave", [47]="Route 2", [48]="Route 2", [49]="Route 2", [50]="Route 2",
    [51]="Viridian Forest", [52]="Pewter City", [53]="Pewter City", [54]="Pewter City", [55]="Pewter City",
    [56]="Pewter City", [57]="Pewter City", [58]="Pewter City", [59]="Mt. Moon", [60]="Mt. Moon",
    [61]="Mt. Moon", [62]="Cerulean City", [63]="Cerulean City", [64]="Cerulean City", [65]="Cerulean City",
    [66]="Cerulean City", [67]="Cerulean City", [68]="Route 4", [69]="Cerulean City", [70]="Route 5",
    [71]="Route 5", [72]="Route 5", [73]="Route 6", [74]="Route 6", [75]="Route 6", [76]="Route 7",
    [77]="Route 7", [78]="Route 7", [79]="Route 8", [80]="Route 8", [81]="Route 10", [82]="Rock Tunnel",
    [83]="Power Plant", [84]="Route 11", [85]="Diglett's Cave", [86]="Route 11", [87]="Route 12",
    [88]="Route 25", [89]="Vermilion City", [90]="Vermilion City", [91]="Vermilion City", [92]="Vermilion City",
    [93]="Vermilion City", [94]="S.S. Anne", [95]="S.S. Anne", [96]="S.S. Anne", [97]="S.S. Anne",
    [98]="S.S. Anne", [99]="S.S. Anne", [100]="S.S. Anne", [101]="S.S. Anne", [102]="S.S. Anne",
    [103]="S.S. Anne", [104]="S.S. Anne", [108]="Victory Road", [113]="Pokemon League", [118]="Pokemon League",
    [119]="Underground Path", [120]="Pokemon League", [121]="Underground Path", [122]="Celadon City",
    [123]="Celadon City", [124]="Celadon City", [125]="Celadon City", [126]="Celadon City",
    [127]="Celadon City", [128]="Celadon City", [129]="Celadon City", [130]="Celadon City",
    [131]="Celadon City", [132]="Celadon City", [133]="Celadon City", [134]="Celadon City",
    [135]="Celadon City", [136]="Celadon City", [137]="Celadon City", [138]="Celadon City",
    [139]="Celadon City", [140]="Celadon City", [141]="Lavender Town", [142]="Pokemon Tower",
    [143]="Pokemon Tower", [144]="Pokemon Tower", [145]="Pokemon Tower", [146]="Pokemon Tower",
    [147]="Pokemon Tower", [148]="Pokemon Tower", [149]="Lavender Town", [150]="Lavender Town",
    [151]="Lavender Town", [152]="Fuchsia City", [153]="Fuchsia City", [154]="Fuchsia City",
    [155]="Fuchsia City", [156]="Safari Zone", [157]="Fuchsia City", [158]="Fuchsia City",
    [159]="Seafoam Islands", [160]="Seafoam Islands", [161]="Seafoam Islands", [162]="Seafoam Islands",
    [163]="Vermilion City", [164]="Fuchsia City", [165]="Pokemon Mansion", [166]="Cinnabar Island",
    [167]="Cinnabar Island", [168]="Cinnabar Island", [169]="Cinnabar Island", [170]="Cinnabar Island",
    [171]="Cinnabar Island", [172]="Cinnabar Island", [173]="Cinnabar Island", [174]="Indigo Plateau",
    [175]="Saffron City", [176]="Saffron City", [177]="Saffron City", [178]="Saffron City",
    [179]="Saffron City", [180]="Saffron City", [181]="Silph Co.", [182]="Saffron City", [183]="Saffron City",
    [184]="Route 15", [185]="Route 15", [186]="Route 16", [187]="Route 16", [188]="Route 16", [189]="Route 12",
    [190]="Route 18", [191]="Route 18", [192]="Seafoam Islands", [193]="Route 22", [194]="Victory Road",
    [195]="Route 12", [196]="Vermilion City", [197]="Diglett's Cave", [198]="Victory Road",
    [199]="Rocket Hideout", [200]="Rocket Hideout", [201]="Rocket Hideout", [202]="Rocket Hideout",
    [203]="Rocket Hideout", [207]="Silph Co.", [208]="Silph Co.", [209]="Silph Co.", [210]="Silph Co.",
    [211]="Silph Co.", [212]="Silph Co.", [213]="Silph Co.", [214]="Pokemon Mansion", [215]="Pokemon Mansion",
    [216]="Pokemon Mansion", [217]="Safari Zone", [218]="Safari Zone", [219]="Safari Zone", [220]="Safari Zone",
    [221]="Safari Zone", [222]="Safari Zone", [223]="Safari Zone", [224]="Safari Zone", [225]="Safari Zone",
    [226]="Cerulean Cave", [227]="Cerulean Cave", [228]="Cerulean Cave", [229]="Lavender Town",
    [230]="Cerulean City", [232]="Rock Tunnel", [233]="Silph Co.", [234]="Silph Co.", [235]="Silph Co.",
    [236]="Silph Co.", [239]="Link Room", [240]="Link Room", [245]="Pokemon League", [246]="Pokemon League",
    [247]="Pokemon League",
}

local GEN2_LANDMARKS = {
    [1]="New Bark Town", [2]="Route 29", [3]="Cherrygrove City", [4]="Route 30", [5]="Route 31",
    [6]="Violet City", [7]="Sprout Tower", [8]="Route 32", [9]="Ruins of Alph", [10]="Union Cave",
    [11]="Route 33", [12]="Azalea Town", [13]="Slowpoke Well", [14]="Ilex Forest", [15]="Route 34",
    [16]="Goldenrod City", [17]="Radio Tower", [18]="Route 35", [19]="National Park", [20]="Route 36",
    [21]="Route 37", [22]="Ecruteak City", [23]="Tin Tower", [24]="Burned Tower", [25]="Route 38",
    [26]="Route 39", [27]="Olivine City", [28]="Lighthouse", [29]="Battle Tower", [30]="Route 40",
    [31]="Whirl Islands", [32]="Route 41", [33]="Cianwood City", [34]="Route 42", [35]="Mt. Mortar",
    [36]="Mahogany Town", [37]="Route 43", [38]="Lake of Rage", [39]="Route 44", [40]="Ice Path",
    [41]="Blackthorn City", [42]="Dragon's Den", [43]="Route 45", [44]="Dark Cave", [45]="Route 46",
    [46]="Silver Cave", [47]="Pallet Town", [48]="Route 1", [49]="Viridian City", [50]="Route 2",
    [51]="Pewter City", [52]="Route 3", [53]="Mt. Moon", [54]="Route 4", [55]="Cerulean City", [56]="Route 24",
    [57]="Route 25", [58]="Route 5", [59]="Underground Path", [60]="Route 6", [61]="Vermilion City",
    [62]="Diglett's Cave", [63]="Route 7", [64]="Route 8", [65]="Route 9", [66]="Rock Tunnel", [67]="Route 10",
    [68]="Power Plant", [69]="Lavender Town", [70]="Lavender Radio Tower", [71]="Celadon City",
    [72]="Saffron City", [73]="Route 11", [74]="Route 12", [75]="Route 13", [76]="Route 14", [77]="Route 15",
    [78]="Route 16", [79]="Route 17", [80]="Route 18", [81]="Fuchsia City", [82]="Route 19", [83]="Route 20",
    [84]="Seafoam Islands", [85]="Cinnabar Island", [86]="Route 21", [87]="Route 22", [88]="Victory Road",
    [89]="Route 23", [90]="Indigo Plateau", [91]="Route 26", [92]="Route 27", [93]="Tohjo Falls",
    [94]="Route 28", [95]="Fast Ship",
}

-- Gen 2 stores each map's landmark in the ROM map header, so read it from there.
-- ROM offset of MapGroupPointers (bank 0x25), English ROMs.
local GEN2_MAP_TABLE = { CRYSTAL = 0x94000, GS = 0x940ED }
local gen2_landmark_cache = {}
local gen2_last_route = nil

local function gen2_landmark(g, group, num)
    if group < 1 or group > 26 or num < 1 then return nil end
    local rom = emu.memory.cart0
    local p = GEN2_MAP_TABLE[g.sub] + (group - 1) * 2
    local ptr = rom:read8(p) + rom:read8(p + 1) * 256
    if ptr < 0x4000 or ptr >= 0x8000 then return nil end
    return rom:read8(0x94000 + (ptr - 0x4000) + (num - 1) * 9 + 5)
end

local function gen2_route_name(g, map_id)
    local cached = gen2_landmark_cache[map_id]
    if not cached then
        local ok, name = pcall(function()
            -- sanity check: group 24 map 4 is New Bark Town, map 3 is Route 29
            if gen2_landmark(g, 24, 4) ~= 1 or gen2_landmark(g, 24, 3) ~= 2 then return nil end
            local id = gen2_landmark(g, math.floor(map_id / 256), map_id % 256)
            if id == 0 then return "" end                    -- "special" maps
            -- Gold/Silver have no Battle Tower, so later landmarks are one lower
            if id and g.sub == "GS" and id >= 29 then id = id + 1 end
            return GEN2_LANDMARKS[id]
        end)
        if ok and name then
            cached = name
            gen2_landmark_cache[map_id] = name
        else
            log_once("WARNING: could not read Gen 2 map names from this ROM; showing map numbers.")
        end
    end
    if cached == "" then cached = gen2_last_route end
    if not cached then return string.format("Map %d-%d", math.floor(map_id / 256), map_id % 256) end
    gen2_last_route = cached
    return cached
end

local function get_route_name(g, map_id, mapsec)
    if g.gen == 3 then
        local group = math.floor(map_id / 256)
        local num = map_id % 256
        if g.family == "FRLG" then return frlg_route_name(group, num) end
        return hoenn_route_name(group, num, mapsec)
    elseif g.gen == 1 then
        return GEN1_MAP_NAMES[map_id] or string.format("Map 0x%02X", map_id)
    end
    return gen2_route_name(g, map_id)
end

local function read_gen3_mon(base)
    local pid  = read32_le(base + 0x00)
    local otid = read32_le(base + 0x04)
    local key  = bxor32(pid, otid)
    local pos_char = string.sub(GEN3_GROWTH_STR, (pid % 24) + 1, (pid % 24) + 1)
    local g_pos = tonumber(pos_char) or 0
    local word0 = read32_le(base + 0x20 + (g_pos * 12))
    local dec0  = bxor32(word0, key)
    local raw_sp = dec0 % 65536
    local dex_sp = gba_species_to_dex(raw_sp)

    local chars = {}
    for i = 0, 9 do
        local b = emu:read8(base + 0x08 + i)
        if b == 0xFF then break end
        table.insert(chars, GBA_CHAR_MAP[b] or "?")
    end

    local level  = emu:read8(base + 0x54)
    local hp     = read16_le(base + 0x56)
    local max_hp = read16_le(base + 0x58)
    local uid    = string.format("G3_%d_%d", otid, pid)

    return {
        uid = uid, nick = table.concat(chars), species = dex_sp,
        hp = hp, max_hp = max_hp, type1 = -1, level = level
    }
end

-- ---------------------------------------------------------------------------
-- Gen 3: menu-aware faint handling
--
-- The old code pressed B five times and then A three times on a fixed timer.
-- Every screen change on the GBA (party -> bag -> battle) takes 30-60 frames
-- and swallows button presses, so some of the B presses never landed and the
-- A presses then re-selected the Potion / "Use" in the bag, which reopened the
-- party menu. Here we read gMain.callback2 (the game's own "which screen am I
-- on" pointer) so we only press A once we are really back on the battle screen.
--
-- gMain layout (pret decomp, same in R/S/E/FR/LG):
--   +0x04 callback2      +0x20/+0x24 vblank counters      +0x439 bit1 inBattle
-- ---------------------------------------------------------------------------
local GEN3_MAIN_CANDIDATES = {
    RS   = { 0x030022C0 },
    E    = { 0x030022C0 },
    FRLG = { 0x030030F0 },
}
local GEN3_CB2_LEARN_FRAMES = 180      -- frames of "inBattle" needed to trust the learned battle callback

local gen3_main = nil                  -- verified gMain base address
local gm_probe, gm_stage, gm_frames = nil, 1, 0
local gm_failed = false
local cb2_hist, cb2_best, cb2_best_n = {}, nil, 0
local gen3_seq = nil                   -- active menu sequence (nil = idle)
local gen3_sleep = nil                 -- foes we put to sleep for the faint turn

local function r32(a)
    return emu:read32(a) % 4294967296
end

local function is_rom_thumb_ptr(v)
    return v >= 0x08000000 and v < 0x0A000000 and (v % 2) == 1
end

local function gm_candidate(base, strict)
    return { base = base, strict = strict, prev1 = nil, prev2 = nil, hits = 0 }
end

-- Fallback when the hard-coded address is wrong: look through IWRAM for something
-- shaped like struct Main (callbacks are ROM pointers at +0/+4/+8/+0xC).
local function gm_scan()
    local found = {}
    for a = 0x03000000, 0x03007C00, 4 do
        local cb2 = r32(a + 4)
        if is_rom_thumb_ptr(cb2) then
            local cb1, sv, vb = r32(a), r32(a + 8), r32(a + 12)
            if (cb1 == 0 or is_rom_thumb_ptr(cb1))
                and (sv == 0 or is_rom_thumb_ptr(sv))
                and (vb == 0 or is_rom_thumb_ptr(vb)) then
                found[#found + 1] = gm_candidate(a, true)
            end
        end
    end
    return found
end

-- gMain is verified by behaviour: callback2 is a ROM pointer and one of the vblank
-- counters ticks up every frame.
local function gm_probe_step()
    if gen3_main or gm_failed then return end
    local g = detect_game()
    if not g or g.gen ~= 3 then return end

    if not gm_probe then
        gm_probe = {}
        for _, a in ipairs(GEN3_MAIN_CANDIDATES[g.family] or {}) do
            gm_probe[#gm_probe + 1] = gm_candidate(a)
        end
    end
    gm_frames = gm_frames + 1

    for _, c in ipairs(gm_probe) do
        local v1, v2, cb2 = r32(c.base + 0x20), r32(c.base + 0x24), r32(c.base + 4)
        if c.prev1 then
            local d1 = (v1 - c.prev1) % 4294967296
            local d2 = (v2 - c.prev2) % 4294967296
            local t1, t2 = (d1 >= 1 and d1 <= 3), (d2 >= 1 and d2 <= 3)
            -- scanned candidates must tick BOTH counters: a base shifted by 4 bytes would only tick one
            local ticking = c.strict and (t1 and t2) or (not c.strict and (t1 or t2))
            if is_rom_thumb_ptr(cb2) and ticking then
                c.hits = c.hits + 1
            end
        end
        c.prev1, c.prev2 = v1, v2
        if c.hits >= 30 then
            gen3_main = c.base
            console:log(string.format("[SoulLink] Verified gMain at 0x%08X (menu-aware faint handling on)", c.base))
            return
        end
    end

    if gm_stage == 1 and gm_frames >= 300 then
        local ok, found = pcall(gm_scan)
        if ok and #found > 0 and #found <= 300 then
            gm_probe, gm_stage, gm_frames = found, 2, 0
        else
            gm_failed = true
        end
    elseif gm_stage == 2 and gm_frames >= 240 then
        gm_failed = true
    end
    if gm_failed then
        console:log("[SoulLink] Could not locate gMain - using timed menu escape (less reliable).")
    end
end

-- Learns BattleMainCB2 = the callback2 value that dominates while inBattle is set.
-- Bag / party / summary screens use other callbacks, so "callback2 != learned value
-- while inBattle" means "a sub menu (or a screen transition) is on screen".
local function gen3_track()
    if not gen3_main then
        gm_probe_step()
        return
    end
    if (math.floor(emu:read8(gen3_main + 0x439) / 2) % 2) == 1 then
        local cb2 = r32(gen3_main + 4)
        local n = (cb2_hist[cb2] or 0) + 1
        cb2_hist[cb2] = n
        if n > cb2_best_n then
            local first = (cb2_best_n < GEN3_CB2_LEARN_FRAMES) and (n >= GEN3_CB2_LEARN_FRAMES)
            cb2_best, cb2_best_n = cb2, n
            if first then
                console:log(string.format("[SoulLink] Learned battle screen callback 0x%08X", cb2))
            end
        end
    end
end

local function gen3_battle_cb2()
    if cb2_best_n >= GEN3_CB2_LEARN_FRAMES then return cb2_best end
    return nil
end

-- true / false once the layout is verified and learned, otherwise nil ("don't know")
local function gen3_in_battle()
    if not (gen3_main and gen3_battle_cb2()) then return nil end
    return (math.floor(emu:read8(gen3_main + 0x439) / 2) % 2) == 1
end

-- ---- foes: sleep them for the one turn our dead Pokemon cannot act ---------
-- (BattlePokemon: +0x28 hp, +0x2C maxHP, +0x48 personality, +0x4C status1, sleep = low 3 bits)
local BM_STRIDE = 0x58

local function gen3_sleep_foes(slot, battler, bm_base, double)
    local addrs = {}
    if bm_base and battler then
        addrs[#addrs + 1] = bm_base + 1 * BM_STRIDE          -- battler 1 (left foe)
        if double then addrs[#addrs + 1] = bm_base + 3 * BM_STRIDE end   -- battler 3 (right foe)
    else
        addrs[#addrs + 1] = slot + BM_STRIDE
    end

    gen3_sleep = gen3_sleep or { foes = {}, deadline = frame_counter + 3600 }
    for _, a in ipairs(addrs) do
        local hp, mhp = read16_le(a + 0x28), read16_le(a + 0x2C)
        local st = emu:read8(a + 0x4C)
        if hp > 0 and mhp > 0 and hp <= mhp and (st % 8) == 0 then
            emu:write8(a + 0x4C, st + 4)
            table.insert(gen3_sleep.foes, { addr = a, pid = read32_le(a + 0x48) })
        end
    end
    gen3_sleep.deadline = frame_counter + 3600
end

-- A sleeping foe skips exactly one action (counter 4 -> 3). As soon as that has
-- happened we wake it again, so it never gets extra free turns.
local function gen3_sleep_step()
    local s = gen3_sleep
    if not s then return end
    local expired = frame_counter > s.deadline
    local keep = {}
    for _, f in ipairs(s.foes) do
        if read32_le(f.addr + 0x48) == f.pid then          -- still the same Pokemon
            local st = emu:read8(f.addr + 0x4C)
            local asleep = st % 8
            if asleep ~= 0 then
                if asleep < 4 or expired then
                    emu:write8(f.addr + 0x4C, st - asleep)
                else
                    keep[#keep + 1] = f
                end
            end
        end
    end
    s.foes = keep
    if #keep == 0 then gen3_sleep = nil end
end

-- ---- menu sequencer --------------------------------------------------------
local SEQ_B_HOLD, SEQ_B_GAP   = 3, 21
local SEQ_A_HOLD, SEQ_A_GAP   = 3, 15
local SEQ_SETTLE              = 45      -- frames on the battle screen before we trust it (fades are over)
local SEQ_TIMEOUT             = 1200
local SEQ_BLIND_B_PRESSES     = 8       -- timed fallback: widely spaced B presses

-- gActionSelectionCursor (per battler): 0 FIGHT, 1 BAG, 2 POKEMON, 3 RUN.
-- If we are on a sub screen and the cursor says POKEMON, the player is on the switch
-- screen, whose HP bars were drawn before the faint -> it needs to be reopened.
local function gen3_on_switch_screen(double)
    local main_cb = gen3_battle_cb2()
    if not (gen3_main and main_cb) then return false end
    if r32(gen3_main + 4) == main_cb then return false end        -- on the battle screen itself
    local gp = get_gen3()
    if not (gp and gp.sel) then return false end
    local a = emu:read8(gp.sel)
    if not double then return a == 2 end
    local b = emu:read8(gp.sel + 2)
    return (a == 2 or b == 2) and a ~= 1 and b ~= 1
end

local function gen3_seq_start(double)
    if gen3_seq then
        gen3_seq.double = gen3_seq.double or double
        return
    end
    gen3_seq = {
        double = double, phase = "escape", t0 = frame_counter,
        stable = 0, hold = 0, gap = 0, key = nil,
        b_main = 0, a_count = 0, blind_b = 0, retries = 0,
        refresh = gen3_on_switch_screen(double), refresh_presses = 0, away = 0,
    }
    console:log("[SoulLink] Faint sequence started (" .. (double and "double" or "single") .. " battle"
        .. (gen3_seq.refresh and ", reloading switch screen" or "") .. ")")
end

local function gen3_seq_finish(reason)
    local s = gen3_seq
    if s and s.key then emu:clearKey(s.key) end
    gen3_seq = nil
    console:log("[SoulLink] Faint sequence finished: " .. reason)
end

local function gen3_seq_press(s, key, hold, gap)
    emu:addKey(key)
    s.key, s.hold, s.gap = key, hold, gap
end

local function gen3_seq_step()
    local s = gen3_seq
    if not s then return end
    local K = C.GBA_KEY

    -- keep the d-pad quiet so the cursor can't be moved while we drive the menus
    emu:clearKey(K.UP)
    emu:clearKey(K.DOWN)
    emu:clearKey(K.LEFT)
    emu:clearKey(K.RIGHT)

    if gen3_in_battle() == false then return gen3_seq_finish("battle ended") end
    if frame_counter - s.t0 > SEQ_TIMEOUT then return gen3_seq_finish("timeout") end

    -- where are we? (evaluated every frame so the settle timer is real frames)
    local main_cb = gen3_battle_cb2()
    local known = (gen3_main ~= nil) and (main_cb ~= nil)
    local in_main = known and (r32(gen3_main + 4) == main_cb)
    if known then
        if in_main then s.stable = s.stable + 1 else s.stable = 0 end
    end

    -- refresh phase: A has been pressed; once we have been off the battle screen for a
    -- moment the switch screen is open again (and now draws the updated HP)
    if known and s.phase == "refresh" and s.refresh_presses > 0 then
        if in_main then
            s.away = 0
        else
            s.away = s.away + 1
            if s.away >= 20 then return gen3_seq_finish("switch screen reloaded") end
        end
    end

    -- release the key we are holding, then wait out the gap before the next press
    if s.hold > 0 then
        s.hold = s.hold - 1
        if s.hold == 0 and s.key then emu:clearKey(s.key); s.key = nil end
        return
    elseif s.gap > 0 then
        s.gap = s.gap - 1
        return
    end
    -- free to press something this frame

    if s.phase == "escape" then
        if known then
            if not in_main then
                -- bag / party / summary / a screen fade: keep backing out, never press A here
                gen3_seq_press(s, K.B, SEQ_B_HOLD, SEQ_B_GAP)
            elseif (not s.double) and (not s.refresh) and s.b_main < 2 then
                -- closes the FIGHT move list if it is open (harmless on the action menu)
                s.b_main = s.b_main + 1
                gen3_seq_press(s, K.B, SEQ_B_HOLD, SEQ_B_GAP)
            elseif s.stable >= SEQ_SETTLE then
                if s.refresh then
                    s.phase = "refresh"
                elseif s.double then
                    return gen3_seq_finish("back on the battle screen (double battle)")
                else
                    s.phase = "fight"
                end
            end
        else
            -- timed fallback (gMain not found): many, well spaced B presses
            if s.blind_b < SEQ_BLIND_B_PRESSES then
                s.blind_b = s.blind_b + 1
                gen3_seq_press(s, K.B, SEQ_B_HOLD, 24)
            elseif s.double then
                return gen3_seq_finish("timed escape done (double battle)")
            else
                s.phase = "fight"
            end
        end

    elseif s.phase == "refresh" then
        if not in_main then return end                         -- already reopening: wait
        if s.refresh_presses >= 3 then return gen3_seq_finish("could not reopen the switch screen") end
        local gp = get_gen3()
        if gp and gp.sel then                                  -- cursor on POKEMON
            emu:write8(gp.sel, 2)
            if s.double then emu:write8(gp.sel + 2, 2) end
        end
        s.refresh_presses = s.refresh_presses + 1
        gen3_seq_press(s, K.A, SEQ_A_HOLD, 30)

    elseif s.phase == "fight" then
        if known and not in_main then
            -- something reopened a sub menu: leave it instead of pressing A inside it
            s.retries = s.retries + 1
            s.phase = "escape"
            if s.retries > 3 then return gen3_seq_finish("gave up after re-entering menus") end
            return
        end
        if s.a_count == 0 then
            local gp = get_gen3()
            if gp and gp.sel then emu:write8(gp.sel, 0) end   -- cursor back on FIGHT
        end
        if s.a_count >= 3 then return gen3_seq_finish("done") end
        s.a_count = s.a_count + 1
        gen3_seq_press(s, K.A, SEQ_A_HOLD, SEQ_A_GAP)
    end
end

-- Gen 2 battle flags (English ROMs). SubStatus4 bit 5 (value 32) = "must recharge".
local function gen2_sub4_addrs(g)
    if g.sub == "CRYSTAL" then return 0xC66B, 0xC670 end   -- player, enemy
    return 0xCB49, 0xCB4E                                  -- Gold / Silver
end

local function set_recharge(addr)
    local v = emu:read8(addr)
    if math.floor(v / 32) % 2 == 1 then return false end   -- was already set
    emu:write8(addr, v + 32)
    return true
end

-- Is this party struct the Pokemon that is currently out in battle?
local function gen2_is_active(g, base)
    local crystal = (g.sub == "CRYSTAL")
    local bm = crystal and 0xC62C or 0xCB0C                -- wBattleMon
    if emu:read8(bm + 0x0D) ~= emu:read8(base + 0x1F) then return false end      -- level
    local p_sub5 = crystal and 0xC66C or 0xCB4A
    if math.floor(emu:read8(p_sub5) / 8) % 2 == 1 then
        -- Transformed: species and DVs are copied from the foe, max HP is not.
        return read16_be(bm + 0x12) == read16_be(base + 0x24)
    end
    return emu:read8(bm) == emu:read8(base)                                      -- species
        and read16_be(bm + 0x06) == read16_be(base + 0x15)                       -- DVs
end

-- ---- Gen 1/2 menu sequencer: back out of bag/party/move menus, then FIGHT ---
-- The screen is read from the tilemap (20x18), where letters use the text codes.
local gb_seq = nil
local GB_TXT_FIGHT    = {0x85,0x88,0x86,0x87,0x93}
local GB_TXT_FAINTED  = {0xA5,0xA0,0xA8,0xAD,0xB3,0xA4,0xA3,0xE7}       -- "fainted!"
local GB_TXT_USE_NEXT = {0x94,0xB2,0xA4,0x7F,0xAD,0xA4,0xB7,0xB3}       -- "Use next"

local function gb_tilemap(g)
    return (g.gen == 2 and g.sub == "CRYSTAL") and 0xC4A0 or 0xC3A0
end

local function gb_text_at(addr, txt)
    for i, b in ipairs(txt) do
        if emu:read8(addr + i - 1) ~= b then return false end
    end
    return true
end

local function gb_screen_has(g, txt)
    local base = gb_tilemap(g)
    for off = 0, 360 - #txt do
        if gb_text_at(base + off, txt) then return true end
    end
    return false
end

-- true only while FIGHT / ITEM / PKMN / RUN is the menu taking input
local function gb_on_battle_menu(g)
    local base = gb_tilemap(g)
    if not gb_text_at(base + 14 * 20 + 10, GB_TXT_FIGHT) then return false end
    for _, row in ipairs({14, 16}) do
        for _, col in ipairs({9, 15}) do
            if emu:read8(base + row * 20 + col) == 0xED then return true end    -- cursor arrow
        end
    end
    return false
end

local function gb_seq_start()
    gb_seq = { t0 = frame_counter, phase = "escape", stable = 0, hold = 0, gap = 12,
               key = nil, a_count = 0, cursor_step = 0 }
end

local function gb_seq_finish(reason)
    if gb_seq and gb_seq.key then emu:clearKey(gb_seq.key) end
    gb_seq = nil
    console:log("[SoulLink] Faint sequence finished: " .. reason)
end

local function gb_seq_press(s, key, gap)
    emu:addKey(key)
    s.key, s.hold, s.gap = key, 3, gap
end

local function gb_seq_step(g)
    local s = gb_seq
    if not s then return end
    local K = C.GB_KEY
    for _, k in ipairs({K.UP, K.DOWN, K.LEFT, K.RIGHT, K.A, K.B}) do
        if k ~= s.key then emu:clearKey(k) end
    end

    local mode = (g.gen == 1) and 0xD057 or ((g.sub == "CRYSTAL") and 0xD22D or 0xD116)
    local hp   = (g.gen == 1) and 0xD015 or ((g.sub == "CRYSTAL") and 0xC63C or 0xCB1C)
    if emu:read8(mode) == 0 then return gb_seq_finish("battle ended") end
    if read16_be(hp) > 0 then return gb_seq_finish("replacement is out") end
    -- Once the game announces the faint, B could answer "no" to the next-Pokemon prompt.
    if gb_screen_has(g, GB_TXT_FAINTED) or gb_screen_has(g, GB_TXT_USE_NEXT) then
        return gb_seq_finish("faint shown")
    end
    if frame_counter - s.t0 > 1200 then return gb_seq_finish("timeout") end

    local on_menu = gb_on_battle_menu(g)
    s.stable = on_menu and (s.stable + 1) or 0

    if s.hold > 0 then
        s.hold = s.hold - 1
        if s.hold == 0 and s.key then emu:clearKey(s.key); s.key = nil end
        return
    elseif s.gap > 0 then
        s.gap = s.gap - 1
        return
    end

    if s.phase == "escape" then
        if not on_menu then
            gb_seq_press(s, K.B, 20)            -- bag, party, move list or battle text
        elseif s.stable >= 10 then
            s.phase = "cursor"
        end
    elseif s.phase == "cursor" then             -- FIGHT is top left
        if not on_menu then s.phase = "escape" return end
        s.cursor_step = s.cursor_step + 1
        if s.cursor_step == 1 then
            if g.gen == 1 then emu:write8(0xCC2D, 0) end
            gb_seq_press(s, K.UP, 8)
        elseif s.cursor_step == 2 then
            gb_seq_press(s, K.LEFT, 8)
        else
            s.phase = "fight"
        end
    else
        if s.a_count >= 3 then return gb_seq_finish("done") end
        s.a_count = s.a_count + 1
        gb_seq_press(s, K.A, 18)
    end
end

local function force_faint_by_uid(target_uid)
    local g = detect_game()
    if not g then return end

    if g.gen == 1 then
        local count = emu:read8(0xD163)
        if count > 6 then count = 0 end
        for i = 0, count - 1 do
            local base = 0xD16B + (i * 0x2C)
            local uid  = string.format("G1_%d_%d", read16_be(base + 0x0C), read16_be(base + 0x1B))
            if uid == target_uid then
                write16_be(base + 0x01, 0)
                if emu:read8(0xD057) > 0 and emu:read8(0xCC2F) == i then
                    write16_be(0xD015, 0)
                    emu:write8(0xD062, 0)
                    emu:write8(0xCCDC, 0)
                    emu:write8(0xCFD2, 0)
                    emu:write8(0xCFD3, 0)
                    emu:write8(0xCFD4, 0)
                    emu:write8(0xCFD5, 0)
                    emu:write8(0xCCDD, 0)
                    emu:write8(0xCCED, 0)
                    emu:write8(0xCCEF, 0)
                    local e_stat = emu:read8(0xD067)
                    if math.floor(e_stat / 32) % 2 == 0 then
                        emu:write8(0xD067, e_stat + 32)
                        clear_enemy_recharge = true
                    else
                        clear_enemy_recharge = false
                    end
                    gb_seq_start()
                end
                console:log("[SoulLink] Partner fainted! Knocked out Gen 1 Pokémon (Slot " .. tostring(i + 1) .. ")")
                return
            end
        end

    elseif g.gen == 2 then
        local p_count_addr = (g.sub == "CRYSTAL") and 0xDCD7 or 0xDA22
        local p_base_addr  = (g.sub == "CRYSTAL") and 0xDCDF or 0xDA2A
        local b_mode_addr  = (g.sub == "CRYSTAL") and 0xD22D or 0xD116
        local b_hp_addr    = (g.sub == "CRYSTAL") and 0xC63C or 0xCB1C
        local p_sub4_addr, e_sub4_addr = gen2_sub4_addrs(g)

        local count = emu:read8(p_count_addr)
        if count > 6 then count = 0 end
        for i = 0, count - 1 do
            local base = p_base_addr + (i * 0x48)
            local uid  = string.format("G2_%d_%d", read16_be(base + 0x06), read16_be(base + 0x15))
            if uid == target_uid then
                write16_be(base + 0x22, 0)
                if emu:read8(b_mode_addr) > 0 and read16_be(b_hp_addr) > 0
                    and gen2_is_active(g, base) then
                    write16_be(b_hp_addr, 0)
                    -- Both sides "recharge": our 0 HP mon cannot attack if it moves
                    -- first, and the foe cannot attack if it moves first.
                    set_recharge(p_sub4_addr)
                    clear_enemy_recharge = set_recharge(e_sub4_addr)
                    gb_seq_start()
                end
                console:log("[SoulLink] Partner fainted! Knocked out Gen 2 Pokémon (Slot " .. tostring(i + 1) .. ")")
                return
            end
        end

    elseif g.gen == 3 then
        local gp = get_gen3()
        if not gp then return end

        local count = emu:read8(gp.pc)
        if count > 6 then count = 0 end
        for i = 0, count - 1 do
            local base = gp.pp + (i * 100)
            local mon  = read_gen3_mon(base)
            if mon and mon.uid == target_uid then
                write16_le(base + 0x56, 0)
                console:log("[SoulLink] Partner fainted! Knocked out Gen 3 Pokémon (Slot " .. tostring(i + 1) .. ")")

                if gen3_in_battle() == false then
                    return      -- overworld / menus outside battle: party HP is all that matters
                end

                local mon_pid = read32_le(base + 0x00)
                local slot, battler, bm_base = find_player_battle_slot(gp, mon_pid)
                if slot and read16_le(slot + 0x28) > 0 then
                    write16_le(slot + 0x28, 0)
                    local double = (read16_le(gp.flags) % 2 == 1) or (battler == 2)
                    gen3_sleep_foes(slot, battler, bm_base, double)
                    gen3_seq_start(double)
                elseif not slot then
                    -- Benched Pokemon: only its party HP changed, so a switch screen that is
                    -- already open still shows the old HP bar. Reload it (no forced attack).
                    -- Skip if one of our active battlers is already dead: that is the
                    -- mandatory replacement screen and we must not touch it.
                    local dbl = (read16_le(gp.flags) % 2 == 1)
                    local active_ok = true
                    for _, bm in ipairs(gp.bm) do
                        if read16_le(bm + 0x28) == 0 or (dbl and read16_le(bm + 0xB0 + 0x28) == 0) then
                            active_ok = false
                        end
                        break
                    end
                    if active_ok and gen3_on_switch_screen(dbl) then
                        gen3_seq_start(dbl)
                    end
                end
                return
            end
        end
    end
end


local pending_faints = {}
local function queue_faint(uid)
    for _, u in ipairs(pending_faints) do
        if u == uid then return end
    end
    table.insert(pending_faints, uid)
end

local function on_received()
    if not sock then return end
    local ok, data = pcall(function() return sock:receive(1024) end)
    if not ok or not data then return end
    for line in string.gmatch(data, "[^\r\n]+") do
        local uid_str = string.match(line, '"uid":%s*"([^"]+)"')
        if string.find(line, '"action":%s*"FAINT"') and uid_str then
            queue_faint(uid_str)
        end
        local assign_str = string.match(line, '"player":%s*(%d+)')
        if string.find(line, '"action":%s*"ASSIGN"') and assign_str then
            PLAYER_ID = tonumber(assign_str)
            console:log("[SoulLink] Assigned as Player " .. tostring(PLAYER_ID) .. "!")
        end
    end
end


local function on_error(err)
    connected = false
    sock = nil
end

local function connect_hub()
    if connected and sock then return true end
    local s = socket.tcp()
    if not s then return false end
    s:add("received", on_received)
    s:add("error", on_error)
    if s:connect(HOST, PORT) then
        sock = s
        connected = true
        console:log("[SoulLink] Connected to hub at " .. HOST .. ":" .. tostring(PORT))
        return true
    end
    pcall(function() s:close() end)
    sock = nil
    return false
end


-- ---------------------------------------------------------------------------
-- Gen 3 PC boxes: report Pokemon that go straight to the PC (party full) so the
-- hub can count them as the area's encounter. PokemonStorage layout (pret):
--   +0x0000 currentBox | +0x0004 boxes[14][30] (80-byte BoxPokemon)
--   +0x8344 boxNames[14][9] | +0x83C2 boxWallpapers[14]
-- FRLG/Emerald keep a pointer to it; Ruby/Sapphire use a fixed EWRAM struct, so
-- we locate it by its shape (default box names + wallpaper ids + valid checksums).
-- ---------------------------------------------------------------------------
local GEN3_STORAGE_PTR = { FRLG = 0x03005010, E = 0x03005D94 }
local BOX_NAMES_OFF, BOX_WALL_OFF, BOX_SLOTS, BOX_SIZE = 0x8344, 0x83C2, 420, 0x83D0
local box_state = { base = nil, tries = 0, next_scan = 0, key = nil, last_send = -100000 }
local box_cache = {}

local function box_storage_valid(b)
    if b < 0x02000000 or b + BOX_SIZE > 0x02040000 then return false end
    if emu:read8(b) > 13 then return false end
    local good = 0
    for i = 0, 13 do
        local n = b + BOX_NAMES_OFF + i * 9
        local term = false
        for j = 0, 8 do
            if emu:read8(n + j) == 0xFF then term = true break end
        end
        if not term then return false end
        local c = emu:read8(n)
        if c >= 0xA1 and c <= 0xEE then good = good + 1 end
        if emu:read8(b + BOX_WALL_OFF + i) > 15 then return false end
    end
    return good >= 12
end

local function box_slots_ok(b)
    for i = 0, BOX_SLOTS - 1 do
        local a = b + 4 + i * 80
        if (read32_le(a) ~= 0 or read32_le(a + 4) ~= 0) and not gen3_checksum_ok(a) then
            return false
        end
    end
    return true
end

local function find_box_storage(allow_scan)
    local g = detect_game()
    local ptr = g and GEN3_STORAGE_PTR[g.family]
    if ptr then
        local b = read32_le(ptr)
        if box_storage_valid(b) and box_slots_ok(b) then return b end
    end
    if ptr and not allow_scan then return nil end
    for b = 0x02000000, 0x02040000 - BOX_SIZE, 4 do
        if emu:read8(b) <= 13 and box_storage_valid(b) and box_slots_ok(b) then return b end
    end
    return nil
end

local function read_box_mons(base)
    local mons = {}
    for i = 0, BOX_SLOTS - 1 do
        local a = base + 4 + i * 80
        local pid, otid = read32_le(a), read32_le(a + 4)
        if pid ~= 0 or otid ~= 0 then
            local ck = read16_le(a + 0x1C)
            local c = box_cache[i]
            if not (c and c.pid == pid and c.otid == otid and c.ck == ck) then
                c = { pid = pid, otid = otid, ck = ck }
                if gen3_checksum_ok(a) then
                    local m = read_gen3_mon(a)
                    if m.species > 0 then c.mon = m end
                end
                box_cache[i] = c
            end
            if c.mon then mons[#mons + 1] = c.mon end
        else
            box_cache[i] = nil
        end
    end
    return mons
end

-- Returns a JSON array body when the PC contents changed (or as a 5 s refresh), else nil.
local function gen3_box_payload()
    local st = box_state
    if frame_counter < st.next_scan then return nil end
    st.next_scan = frame_counter + 30
    if not st.base then
        if st.tries >= 12 then
            log_once("WARNING: could not locate the PC box storage; boxed catches will not be tracked.")
            return nil
        end
        st.tries = st.tries + 1
        st.base = find_box_storage(st.tries > 3)
        if not st.base then
            st.next_scan = frame_counter + 120
            return nil
        end
        console:log(string.format("[SoulLink] Found PC box storage at 0x%08X", st.base))
    elseif not box_storage_valid(st.base) then
        st.base, st.tries, box_cache = nil, 0, {}
        return nil
    end
    local mons = read_box_mons(st.base)
    local parts, uids = {}, {}
    for _, m in ipairs(mons) do
        uids[#uids + 1] = m.uid
        parts[#parts + 1] = string.format('{"uid":"%s","nick":"%s","species":%d}',
            m.uid, (m.nick:gsub('"', '')), m.species)
    end
    local key = table.concat(uids, ",")
    if key == st.key and frame_counter - st.last_send < 300 then return nil end
    st.key, st.last_send = key, frame_counter
    return table.concat(parts, ",")
end


-- ---------------------------------------------------------------------------
-- Gen 1 / Gen 2 PC box (current box only): report Pokemon sent straight to the box.
--   Gen 1: the open box is mirrored in WRAM at 0xDA80 (count, species[21], mons[20]x33,
--          OT[20]x11, nicks[20]x11); wCurrentBoxNum is at 0xD5A0 (low 7 bits).
--   Gen 2: the open box lives only in cart SRAM: 0x2D10 (Crystal) / 0x2D6C (Gold/Silver)
--          (count, species[21], mons[20]x32, OT[20]x11, nicks[20]x11).
-- Only the open box is visible, so the hub treats a big change as a box swap.
-- ---------------------------------------------------------------------------
local gb_box_state = { key = nil, last_send = -100000 }

local function read_gen1_box()
    local cnt = emu:read8(0xDA80)
    if cnt > 20 then return nil end
    local mons = {}
    for i = 0, cnt - 1 do
        local base = 0xDA96 + i * 33
        local dex = GEN1_TO_DEX[emu:read8(base)]
        if dex then
            mons[#mons + 1] = {
                uid = string.format("G1_%d_%d", read16_be(base + 0x0C), read16_be(base + 0x1B)),
                nick = (read_gb_nick(0xDE06, i, 0x0B):gsub('"', '')),
                species = dex,
            }
        end
    end
    local id = emu:read8(0xD5A0) % 128
    if id > 11 then id = nil end
    return mons, id
end

-- Gen 1 raises the party count and shows the nickname screen BEFORE it writes the
-- new Pokemon's data, so a fresh slot holds blank or leftover bytes for a while.
local function gen1_slot_ready(i, seen)
    local base    = 0xD16B + (i * 0x2C)
    local species = emu:read8(base)
    if not GEN1_TO_DEX[species] or species ~= emu:read8(0xD164 + i) then return false end
    local level = emu:read8(base + 0x21)
    if level < 1 or level > 100 or read16_be(base + 0x22) == 0 then return false end
    if not GB_CHAR_MAP[emu:read8(0xD2B5 + i * 0x0B)] then return false end
    -- leftovers of a deposited/shifted Pokemon repeat an ID that already exists
    return not seen[string.format("G1_%d_%d", read16_be(base + 0x0C), read16_be(base + 0x1B))]
end

local function read_gen2_box(g)
    local ok, mem = pcall(function() return emu.memory.sram end)
    if not ok or not mem then
        log_once("WARNING: cart SRAM is not readable from Lua; Gen 2 boxed catches will not be tracked.")
        return nil
    end
    local base = (g.sub == "CRYSTAL") and 0x2D10 or 0x2D6C
    local cnt = mem:read8(base)
    if cnt > 20 or mem:read8(base + 1 + cnt) ~= 0xFF then return nil end
    local mons = {}
    for i = 0, cnt - 1 do
        local mb = base + 22 + i * 32
        local sp = mem:read8(mb)
        if sp >= 1 and sp <= 251 then
            local chars = {}
            local nb = base + 22 + 640 + 220 + i * 11
            for j = 0, 9 do
                local b = mem:read8(nb + j)
                if b == 0x50 then break end
                chars[#chars + 1] = GB_CHAR_MAP[b] or "?"
            end
            mons[#mons + 1] = {
                uid = string.format("G2_%d_%d", mem:read8(mb + 6) * 256 + mem:read8(mb + 7),
                                    mem:read8(mb + 0x15) * 256 + mem:read8(mb + 0x16)),
                nick = table.concat(chars):gsub('"', ''),
                species = sp,
            }
        end
    end
    return mons, nil
end

-- Returns (json body, box_id) when the open box changed (or as a 5 s refresh), else nil.
local function gb_box_payload(mons, id)
    if not mons then return nil end
    local parts, uids = {}, {}
    for _, m in ipairs(mons) do
        uids[#uids + 1] = m.uid
        parts[#parts + 1] = string.format('{"uid":"%s","nick":"%s","species":%d}', m.uid, m.nick, m.species)
    end
    local key = tostring(id) .. "|" .. table.concat(uids, ",")
    local st = gb_box_state
    if key == st.key and frame_counter - st.last_send < 300 then return nil end
    st.key, st.last_send = key, frame_counter
    return table.concat(parts, ","), id
end

-- ---- Poke Ball unlock ------------------------------------------------------
-- Tracking waits for the first Poke Balls, then stays on for that save even if
-- you run out. Unlocked saves are remembered by trainer ID in a small file next
-- to this script, so reloading the script or restarting mGBA keeps them on.
local SAVE_DIR = nil  -- set by the launcher in the copy it puts in each save folder
local BALL_FILE = (function()
    if SAVE_DIR then return SAVE_DIR .. "/soullink_balls_p1.txt" end
    local ok, dir = pcall(function()
        return debug.getinfo(1, "S").source:match("^@(.*[/\\])")
    end)
    return ((ok and dir) or "") .. "soullink_balls_p" .. tostring(PLAYER_ID) .. ".txt"
end)()

local balls_unlocked = {}
pcall(function()
    local f = io.open(BALL_FILE, "r")
    if not f then return end
    for line in f:lines() do balls_unlocked[(line:gsub("%s", ""))] = true end
    f:close()
end)

local function unlock_balls(key)
    balls_unlocked[key] = true
    local ok = pcall(function()
        local f = assert(io.open(BALL_FILE, "a"))
        f:write(key, "\n")
        f:close()
    end)
    if not ok then
        log_once("WARNING: could not save " .. BALL_FILE .. "; the Poke Ball unlock only lasts until the script reloads.")
    end
end

-- keys: one per party Pokemon, built from its original trainer ID
local function balls_latch(has_now, keys)
    for _, k in ipairs(keys) do
        if balls_unlocked[k] then return true end
    end
    if not has_now or #keys == 0 then return false end
    for _, k in ipairs(keys) do
        if not balls_unlocked[k] then unlock_balls(k) end
    end
    console:log("[SoulLink] Poke Balls obtained - encounter tracking is on for this save.")
    return true
end

local latched_loc = nil
local function serialize_state()
    local g = detect_game()
    local items = {}
    local map_id, battle_type, enemy_sp, balls_flag = 0, 0, 0, "true"
    local box_json, box_id = nil, nil
    local mapsec = nil
    local owner_keys = {}

    if g.gen == 1 then
        local count = emu:read8(0xD163)
        if count > 6 then count = 0 end
        map_id      = emu:read8(0xD35E)
        battle_type = emu:read8(0xD057)
        enemy_sp    = GEN1_TO_DEX[emu:read8(0xCFE5)] or 0

        local b_cnt = emu:read8(0xD31D)
        if b_cnt > 20 then b_cnt = 20 end
        balls_flag = "false"
        for i = 0, b_cnt - 1 do
            local iid = emu:read8(0xD31E + (i * 2))
            if iid >= 0x01 and iid <= 0x04 then balls_flag = "true" break end
        end

        local seen = {}
        if count > 0 then
            local box_mons, id = read_gen1_box()
            for _, m in ipairs(box_mons or {}) do seen[m.uid] = true end
            box_json, box_id = gb_box_payload(box_mons, id)
        end

        for i = 0, count - 1 do
          if gen1_slot_ready(i, seen) then
            local base    = 0xD16B + (i * 0x2C)
            local dex_sp  = GEN1_TO_DEX[emu:read8(base + 0x00)] or 0
            local hp      = read16_be(base + 0x01)
            local t1      = GB_TYPE_NORM[emu:read8(base + 0x05)] or 0
            local uid     = string.format("G1_%d_%d", read16_be(base + 0x0C), read16_be(base + 0x1B))
            local level   = emu:read8(base + 0x21)
            local max_hp  = read16_be(base + 0x22)
            local nick    = read_gb_nick(0xD2B5, i, 0x0B):gsub('"', '')
            table.insert(items, string.format(
                '{"uid":"%s","nick":"%s","species":%d,"hp":%d,"max_hp":%d,"type1":%d,"level":%d}',
                uid, nick, dex_sp, hp, max_hp, t1, level
            ))
            seen[uid] = true
            owner_keys[#owner_keys + 1] = "G1_" .. read16_be(base + 0x0C)
          end
        end

    elseif g.gen == 2 then
        local p_count_addr = (g.sub == "CRYSTAL") and 0xDCD7 or 0xDA22
        local p_base_addr  = (g.sub == "CRYSTAL") and 0xDCDF or 0xDA2A
        local n_base_addr  = (g.sub == "CRYSTAL") and 0xDE41 or 0xDB8C
        local m_grp_addr   = (g.sub == "CRYSTAL") and 0xDCB5 or 0xDA00
        local b_mode_addr  = (g.sub == "CRYSTAL") and 0xD22D or 0xD116
        local e_sp_addr    = (g.sub == "CRYSTAL") and 0xD206 or 0xD0EF

        local count = emu:read8(p_count_addr)
        if count > 6 then count = 0 end
        map_id      = (emu:read8(m_grp_addr) * 256) + emu:read8(m_grp_addr + 1)
        battle_type = emu:read8(b_mode_addr)
        enemy_sp    = emu:read8(e_sp_addr)

        -- Balls pocket: count, then (item, quantity) pairs, then 0xFF
        local balls_addr = (g.sub == "CRYSTAL") and 0xD8D7 or 0xD5FC
        local b_cnt = emu:read8(balls_addr)
        balls_flag = tostring(b_cnt >= 1 and b_cnt <= 12
            and emu:read8(balls_addr + 1 + b_cnt * 2) == 0xFF)

        if count > 0 then box_json, box_id = gb_box_payload(read_gen2_box(g)) end

        for i = 0, count - 1 do
            local base   = p_base_addr + (i * 0x48)
            local dex_sp = emu:read8(base + 0x00)
            local uid    = string.format("G2_%d_%d", read16_be(base + 0x06), read16_be(base + 0x15))
            local level  = emu:read8(base + 0x1F)
            local hp     = read16_be(base + 0x22)
            local max_hp = read16_be(base + 0x24)
            local nick   = read_gb_nick(n_base_addr, i, 0x0B):gsub('"', '')
            owner_keys[#owner_keys + 1] = "G2_" .. read16_be(base + 0x06)
            table.insert(items, string.format(
                '{"uid":"%s","nick":"%s","species":%d,"hp":%d,"max_hp":%d,"type1":-1,"level":%d}',
                uid, nick, dex_sp, hp, max_hp, level
            ))
        end

    elseif g.gen == 3 then
        local gp = get_gen3()
        balls_flag = "false"                 -- only a real ball in the pocket counts
        local count = emu:read8(gp.pc)
        if count > 6 then count = 0 end

        local flags      = read32_le(gp.flags)
        local flag_train = (math.floor(flags / 8) % 2) == 1          -- BATTLE_TYPE_TRAINER
        local is_trainer = flag_train
        if not GEN3_STRICT_TRAINER_FLAG then
            is_trainer = flag_train or (read32_le(gp.ep + 0x04) ~= 0)  -- legacy (always true in practice)
        end
        local enemy = read_gen3_mon(gp.ep)
        -- gEnemyParty keeps the last foe after the battle ends, so without this gate
        -- the hub sees "battling X" forever (and files bogus encounters in new areas).
        local in_b = gen3_in_battle()          -- true / false / nil (not learned yet)
        if enemy.species > 0 and enemy.hp > 0 and in_b ~= false then
            battle_type = is_trainer and 2 or 1
            enemy_sp = enemy.species
        end

        local sb1 = gp.sb1
        if gp.sb1_is_ptr then sb1 = read32_le(gp.sb1) end
        if sb1 >= 0x02000000 and sb1 < 0x02040000 then
            map_id = (emu:read8(sb1 + 0x04) * 256) + emu:read8(sb1 + 0x05)
            local ball_pocket = sb1 + gp.ball_off
            balls_flag = "false"
            for i = 0, gp.ball_n - 1 do
                local item_id = read16_le(ball_pocket + (i * 4))
                if item_id >= 1 and item_id <= 12 then
                    balls_flag = "true"
                    break
                end
            end
        end
        if gp.hdr then
            local ms = emu:read8(gp.hdr + 0x14)      -- MapHeader.regionMapSectionId
            if ms <= 84 then mapsec = ms end
        end

        if count > 0 then box_json = gen3_box_payload() end

        for i = 0, count - 1 do
            local mon = read_gen3_mon(gp.pp + (i * 100))
            if gen3_checksum_ok(gp.pp + (i * 100)) then
                owner_keys[#owner_keys + 1] = "G3_" .. read32_le(gp.pp + (i * 100) + 4)
            end
            local nick = mon.nick:gsub('"', '')
            table.insert(items, string.format(
                '{"uid":"%s","nick":"%s","species":%d,"hp":%d,"max_hp":%d,"type1":-1,"level":%d}',
                mon.uid, nick, mon.species, mon.hp, mon.max_hp, mon.level
            ))
        end
    end

    balls_flag = tostring(balls_latch(balls_flag == "true", owner_keys))

    local route = get_route_name(g, map_id, mapsec):gsub('"', '')
    if battle_type ~= 0 and latched_loc then
        map_id, route = latched_loc.map_id, latched_loc.route
    elseif battle_type == 0 then
        latched_loc = { map_id = map_id, route = route }
    end
    return string.format(
        '{"player":%d,"gen":%d,"sub":"%s","map_id":%d,"route":"%s","battle_type":%d,"enemy_species":%d,"has_balls":%s,"party":[%s]%s}\n',
        PLAYER_ID, g.gen, tostring(g.sub or "RBY"), map_id, route, battle_type, enemy_sp, balls_flag, table.concat(items, ","),
        box_json and (',"box":[' .. box_json .. ']' .. (box_id and (',"box_id":' .. box_id) or "")) or ""
    )
end


local function on_frame()
    local g = detect_game()

    if g.gen == 3 then gen3_track() end

    -- Apply every queued FAINT at once (a double KO sends two), but never while
    -- a previous faint sequence is still driving the menus.
    if #pending_faints > 0 and not gb_seq and not gen3_seq then
        local queued = pending_faints
        pending_faints = {}
        for _, uid in ipairs(queued) do
            local ok, err = pcall(force_faint_by_uid, uid)
            if not ok then console:log("[SoulLink] Error applying faint: " .. tostring(err)) end
        end
    end

    if g.gen == 3 then
        gen3_sleep_step()
        gen3_seq_step()
    end

    if clear_enemy_recharge then
        if g.gen == 1 and emu:read8(0xD057) > 0 and read16_be(0xD015) > 0 then
            local e_stat = emu:read8(0xD067)
            if math.floor(e_stat / 32) % 2 == 1 then emu:write8(0xD067, e_stat - 32) end
            clear_enemy_recharge = false
        elseif g.gen == 2 then
            local b_mode = (g.sub == "CRYSTAL") and 0xD22D or 0xD116
            local b_hp   = (g.sub == "CRYSTAL") and 0xC63C or 0xCB1C
            local _, e_sub4 = gen2_sub4_addrs(g)
            if emu:read8(b_mode) > 0 and read16_be(b_hp) > 0 then
                local e_stat = emu:read8(e_sub4)
                if math.floor(e_stat / 32) % 2 == 1 then emu:write8(e_sub4, e_stat - 32) end
                clear_enemy_recharge = false
            end
        end
    end


    if g.gen ~= 3 then gb_seq_step(g) end

    frame_counter = frame_counter + 1
    if frame_counter % 15 ~= 0 then return end
    if not connect_hub() then return end

    local ok = sock:send(serialize_state())
    if not ok then
        connected = false
        sock = nil
    end
end

callbacks:add("frame", on_frame)
console:log("[SoulLink] Multi-Gen Bridge (Gen 1/2/3) Loaded — waiting for Player assignment...")
