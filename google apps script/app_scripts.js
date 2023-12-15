// MrZJA9h0Gmrbl4GDIfYazIpMs7zNMImyn

/**
 * Замена значения из одного столбца соответсвующим ему значением из другого. Аналог vlookup, но с более простым синтаксисом.
 * replaceValue(Что искать; столбец где ищем; солбец чем заменяем).
 *
 * @param {string} value
 * Значение которое нужно заменить \ Массив значений для замены
 * @param {array} source
 * Столбец справочника содержащий искомые значения
 * @param {array} destination
 * Столбец справочника содержащий значения для подстановки
 * @return {string}
 * @customfunction
 */
function replaceValue(value, source, destination) {
  source = everyElementToString(source) // Перевод всех элементов в строки
  return replaceValueCore(value, source, destination)
}

function replaceValueCore(value, source, destination) {
  var index = ""

  if (!value.map) {
    if (isNotEmpty(value)) {
      index = source.indexOf(String(value))
      if (index != -1) {
        return String(destination[index])
      }
    }
    return ""
  }

  var out = value.map(function(element) {
    return replaceValueCore(element, source, destination)
  })

  return out

}

/**
 * Переводит все элементы массива в строки
 *
 * @param {array} iterable Массив.
 * @customfunction
 */
function everyElementToString(iterable, filter) {
  if (!iterable.map) {return String(iterable)}
  if (filter) {iterable = purgeArray(iterable)}

  var out = iterable.map(function(item) {
    return String(item)
  })

  return out
}


/**
 * Удаляет из массива пустые ячейки и ячейки начинающиеся с запретных символов.
 *
 * @param {array} iterable Набор диапазонов.
 * @param {string} disabled_letters Запретные символы (строка, может состоят из одного элемента). В итоговый массив не выключаются элементы начинающиеся с этой строки
 * @returns Массив (столбец) элементов.
 * @customfunction
 */
function purgeArray(iterable, disabled_letters) {
  if (disabled_letters) {disabled_letters_length = disabled_letters.length} else {disabled_letters_length = 0}
  if (!iterable.map) {return iterable}

  iterable = reduceOneLineArray(iterable)
  var out = iterable.filter(function(row) {
    return any(row) & String(row[0]).substring(0, disabled_letters_length) != disabled_letters
  })

  return reduceOneLineArray(out)
}

/**
 * Вытаскивает внутренний массив если он всего один.
 *
 * @param {array} iterable Массив.
 * @customfunction
 */
function reduceOneLineArray(iterable) {
  if (iterable.length == 1 & Array.isArray(iterable[0])) {return iterable[0]}
  return iterable
}

/**
 * Математическое огругление с заданным числом значений после запятой.
 *
 * @param {float} value – Округляемое число
 * @param {int} round – Количество знаков после запятой
 * @returns {float} Округлённое значение
 * @customfunction
 */
function roundPlus(value, digit) {
  if(isNaN(value)) return false;
  digit = digit || 2;

  return parseFloat(value.toFixed(digit))
}

/**
 * Считает мат. ожидание значений указанных с их весом.
 *
 * @param {array} valueSet – Столбец значений
 * @param {array} weightSet – Столбец весов с которыми выпадают соответствующие значения
 * @returns {float} Значение мат. ожидания значения
 * @customfunction
 */
function expectedValue(valueSet, weightSet) {
  var cap = elementSum(weightSet);
  var out = [];

  for (var i = 0; i < valueSet.length; i++) {
    out[i] = valueSet[i] * (weightSet[i] / cap);
  }

  return elementSum(out);
}

// Сумма элементов массива
function elementSum(dataset) {
  var sum = dataset.reduce(function (acc, currValue) {
  return acc + Number(currValue)}, 0);

  return sum;
}

/**
 * Нумерует элементы массива.
 *
 * @param {array}  array Столбец элементы которого необходимо пронумерова.
 * @param {int} factor Множитель на которые необходимо умножить порадковый номер элемента массива. Не обязательно! По умолчанию равен единице.
 * @returns Массив (столбец) элементов.
 * @customfunction
 */
function countArrayElement(array, factor) {
  var factor = factor || 1
  var result = []
  var j = 1

  for (var i = 0; i < array.length; i++) {
    if (any(array[i])) {
      result[i] = j * factor;
      j++
      }
    }

  return result;
}

/**
 * Склеивает несколько массивов в один, принимает как строки так и столбцы.
 * Допустимо наличие пропусков в используемых массивах.
 *
 * @param {Sheet1!A1:C5} value Набор диапазонов.
 * @returns Массив (столбец) элементов.
 * @customfunction
 */
function mergeArray() {
  var result = [];

  for (var i = 0; i < arguments.length; i++) {
    result = result.concat(purgeArray(arguments[i]))
  }

  return result
}

function searchParent(ids, tree, i, layer) {
  for (var j = i; j >= 0 ; j--) {
    if (tree[j][layer] != '') {
      return String(ids[j])
    }
  }
}

/**
 * Разворачивает дерево в плоскую структуру с указанием уровня иерархиии и родителя.
 * ID категории; Уровень в иерархии (1-3); Родитель категории.
 *
 * @customfunction
 */
function categoryTree(ids, tree) {
//  [Строка][Столбец]
  var out = []

  ids = purgeArray(ids)

  for (var i = 0; i < ids.length; i++) {
    out[i] = []
    out[i][0] = String(ids[i]) // Имя

    if (tree[i][1] == '' & tree[i][0] == '') {
      out[i][1] = 3 // Слой
      out[i][2] = searchParent(ids, tree, i, 1) // Родитель

    } else if (tree[i][0] == '') {
      out[i][1] = 2
      out[i][2] = searchParent(ids, tree, i, 0)

    } else {
      out[i][1] = 1
      out[i][2] = ''
    }

  }
  return out
}

/**
 * true – если хотя бы один элемент не пустой
 *
 * @param {array} Массив для проверки.
 * Массив элементов для проверки
 */
function any(iterable) {
  if (!iterable.map) {
    return isNotEmpty(iterable)
  }

  return iterable.some(isNotEmpty)
}

/**
 * true – если все элементы не пустые
 *
 * @param {array} Массив для проверки.
 * Массив элементов для проверки
 */
function all(iterable) {
  if (!iterable.map) {
    return isNotEmpty(iterable)
  }

  return iterable.every(isNotEmpty)
}

function isNotEmpty(item) {
  return String(item).length > 0
}


/**
 * Работает аналогично штатной join. Принимает двумерный массивы и склеивает содержимое строк в массиве через разделитель.
 * Возвращает столбец из склееных элементов строк исходного массива.
 *
 * @param {string} sep Разделитель через который будет склеиваться содержимое строк.
 * @param {array} data Массивы строк для склеивания.
 * @customfunction
 */
function joinStrings(sep, data) {
  var out = data.map(function(row) {
    return row.filter(function(item){return isNotEmpty(item)}).join(sep)
  })

  return out
}

/**
 * Расширение функции joinStrings. Склеивает всё содержимое блока через разделители. Внутри одной строки – внутренний разделитель,
 * если блок из нескольких строк, то они склеиваются через внешний разделитель.
 * Данные начала блока указываются из вне. Блок – расстояние от одной запоненной строки до другой. Каждая заполненная строка – отдельный блок.
 *
 * @param {Опа!} sepInt Разделитель через который склеиваются данные внутри строки
 * @param {string} sepExt Разделитель через который склеиваются разные строки блока
 * @param {array} block_info Донор информации для разделения блоков. Блоком считается расстояние между записями в столбце.
 * Например, если донором взять столбец с ключамии, то блоком будет содержимое строк от одного ключа (включая), до другого (не включая)
 * @param {array} data Столбец с информацией которую нужно склеивать
 * @param {string} br Обрамляющие скобки. Не обязательно
 * @return {array} Возвращает что-то
 * @customfunction
 */
function joinStringsBlock(sepInt, sepExt, block_info, data, br) {
  var br = br || ""
  var out = []
  var bufer = []

  var intervals = defineOneLineBlockPlus(block_info)

  for (var i = 0; i < intervals.length; i += 2) {
    bufer = joinAndReduce(sepInt, data.slice(intervals[i], intervals[i+1]))
    bufer = bufer.join(sepExt)

    if (br.length > 1 & any(bufer)) {
        bufer = br[0] + bufer + br[1]
    }

    out[intervals[i]] = bufer
    bufer = []
  }

  return out;
}

function joinAndReduce(sep, iterable) {
  iterable = iterable.filter(function(row){
    return all(row)
  })

  var out = iterable.reduce(function(acc, row){
    return acc.concat(row.join(sep))
    }, [])

  return out
}

/**
 * Проверка на корректность указания виртуальных слотов в списке.
 *
 * @param {strings array} slots
 * Столбец со списком виртуальных слотов используемых в предметах.
 * @param {array} dict
 * Массив со списком всех доступных виртуальных слотов.
 * @return The converted base.
 * @customfunction
 */
function checkSlotsError(slots, dict) {
  dict = everyElementToString(dict, true) // Чистит массив от пустых элементо и переводит все оставшиеся в строки
  slots = everyElementToString(slots, true)
  var out = []

  for (var i = 0; i < slots.length; i++) {
    var bufer = slots[i].split(", ")
    for(var j = 0; j < bufer.length; j++) {
      if (dict.indexOf(bufer[j]) == -1) {
        out[i] = "ALARM"
      }
    }
  }

  if (out.length == 0) {
    return "CORRECT"
  }

  return out
}

function purgeName(string) {

  var start = string[0]
  var end = string.slice(-4)

  if (start == "#") {
    string = string.slice(1)
  }

  if (end == "_tmp") {
    string = string.slice(0, -4)
  }

  return string
}

// Определяет расстояние между записями в столбце. Блок начинается от одной записи и до следующей не включая. Несколько записей подряд считаются одним блоком.
function defineBlock(data) {
  var new_block = true
  var out = []

  for (var i = 0; i < data.length; i++) {
    if (!isNotEmpty(data[i][0]) & !new_block) {
      new_block = true
      out.push(i)


    } else if (isNotEmpty(data[i][0]) & new_block) {
      new_block = false
      out.push(i)
    }
  }

return out
}

// Блок начинается от одной группы записей и до следующей, не включая. Пустоты между блоками относятся к вышестоящему блоку.
function defineBlockPlus(data) {
  var new_block = true
  var out = []

  for (var i = 0; i < data.length; i++) {
    if (!isNotEmpty(data[i][0]) & !new_block) {
      new_block = true


    } else if (isNotEmpty(data[i][0]) & new_block) {
      new_block = false
      out.push(i)
      if (out.length > 1) {
        out.push(i)
      }
    }
  }

out.push(data.length)
return out
}

// Блок – каждая заполненнаю строку и только заполненная строка.
// ВАЖНО! Расстояние между строками не попадает в блок!
function defineOneLineBlock(data) {
  var out = []

  for (var i = 0; i < data.length; i++) {
//    if (isNotEmpty(data[i][0])) {
    if (all(data[i])) {
      out.push(i)
      out.push(i+1)
    }
  }

return out
}

// Блок начинается от одной запоненной строки до другой, не включая. Пустые строки между блоками относятся к вышестоящему блоку.
function defineOneLineBlockPlus(data) {
  var out = []
  var flag = false // флаг первого элемента последовательночти

  for (var i = 0; i < data.length; i++) {
//    if (isNotEmpty(data[i][0])) {
    if (all(data[i])) {
      out.push(i)
      if (flag) {
        out.push(i)
      }
      flag = true
    }
  }

  out.push(data.length)
  return out
}

/**
 * Склеивание данных с заголовкам в формате names[0] = data[0][0], names[1] = data[0][1], names[2] = data[0][2] | names[1] = data[1][0], ...
 * ВАЖНО! В массиве с названиями должно быть хота бы 2 элемента.
 * Автоматически откусывает @ от начала заголовков и _tmp от конца в именах.
 *
 * @param {array} names
 * Строка с заголовками данных.
 * @param {array} data
 * Массив с данным под заголовками.
 * @return {string} result
 * Данные склеены в одну строку
 * @customfunction
 */
function toConfig(names_array, data_array, br) {
  var br = br || ""
  var txt = br[0] || ""
  var txt_end = br.slice(-1) || ""

  var sepInt = ", "  // Разделитель данных внутри блока
  var sepBlock = " | "  // Разделитель блоков
  var sepString = " = "  // Разделитель внутри строки

  // Откусывает префикс "#" и суффикс "_tmp", если они есть
  names_array = names_array[0].map(function(element) {
    return purgeName(element)
  })

  for (var i = 0; i < data_array.length; i++) {
    if (any(data_array[i])) {

      // line_length = names_array.length
      line_length = row_length(data_array[i])

      if (i > 0) {
        txt += sepBlock
      }

      for (var j = 0; j < line_length; j++) {
        // Составление строки, название = значение. Разделитель sepString
        txt += names_array[j] + sepString + data_array[i][j];

        // Разделитель элементов если еще не все элементы из строки перебрали
        if (j < line_length - 1) {
          txt += sepInt
        }
      }

    }
  }

  if (txt == br[0]) {
    return ""
  }

  return txt + txt_end
}

function row_length(iterable) {
  iterable = iterable.filter(function(element){
    return isNotEmpty(element)
  })

  return iterable.length
}


/**
 * Расширение функции toConfig. Склеивает блоки с информацией в строки конфига. Разделение на блоки задается отдельно.
 * @param {array} headers Строка с заголовками данных.
 * @param {array} block_info Донор информации для разделения блоков.
 * @param {array} data Массив с данными под заголовками.
 * @param {string} block_function Тип функции разбиения на блоки line, lineplus, block, blockplus (по умолчанию).
 * line - Блок – каждая заполненную строку и только заполненная строка. Расстояние между строками не попадает в блок.
 * lineplus - Блок начинается от одной запоненной строки до другой, не включая. Пустоты между строками относятся к вышестоящему блоку.
 * block - Блок начинается от одной записи и до следующей не включая. Несколько записей подряд считаются одним блоком.
 * blockplus - Блок начинается от одной группы записей и до следующей, не включая. Несколько записей подряд считаются одним блоком, пустоты между блоками относятся к вышестоящему блоку.
 * @param {string} br Обрамляющие строку скобки, Например: "{}".
 * @return {string} result Массив строк соответствующих блокам. Строки располагаются в начале блока.
 * @customfunction
 */
function toConfigBlock(headers, block_info, data, block_function, br) {
  var out = []
  var intervals = []
  var block_function = block_function || "blockplus"

  switch(block_function) {
    case "line":
      var func = defineOneLineBlock
      break
    case "lineplus":
      var func = defineOneLineBlockPlus
       break
    case "block":
      var func = defineBlock
      break
    case "blockplus":
      var func = defineBlockPlus
      break
  }

  intervals = func(block_info)

  for (var i = 0; i < intervals.length; i += 2) {
    out[intervals[i]] = toConfig(headers, data.slice(intervals[i], intervals[i+1]), br)
  }

  if (out.length == 0) {
    return ""
  }

 return out;
}

/**
 * Генератор раскладывает значение на составляющие со своим весом от 2 до 3х элементов
 * Например 0,25 будет разложено на 0 с весом 750 и 1 с весом 250
 *
 * @param {float} target
 * Значение мат. ожидания которого необходимо достичь.
 * @param {bool} zero
 * Не обязательно. false по умолчанию. true – если нужен ли ноль для значений мат. ожидания в интервал [1; 1.5).
 * Например: 1.3 будет разложен в 0: 100, 1: 500, 2: 400 если true и 1: 700, 2: 300.
 * @return {array} result
 * Столбец значений и стлбец весов для этих значений.
 * @customfunction
 */
function countWeightGenerator(target, zero) {
  zero = zero || false
  target = roundPlus(target)

  var cap = 1000
  var delta = 1
  var t = Math.round(target)
  if ((target >= 0.5 & target < 1) || (t - target == 0.5))
    {
      var num = [t - 1, t]
      var weights = [cap/2, cap/2]

    } else if  ((zero == 1 & target >= 1) || (t > 1) || (target == 1)) {
      var num = [t - 1, t, t + 1]
      var weights = [cap/4, cap/2, cap/4]

    } else {
      var num = [t, t + 1]
      var weights = [cap/2, cap/2]
    }

  var value = 0
  while (Math.abs(value - target) > 0.001){
    if (value > target) {
      weights[0] += delta
      weights[weights.length - 1] -= delta;
    } else if (value < target) {
      weights[0] -= delta
      weights[weights.length - 1] += delta
    }

    value = expectedValue(num, weights)
  }

  var out = []
  for (var i = 0; i < num.length; i++) {
    out[i] = [num[i], weights[i]];
  }

  return out
}
