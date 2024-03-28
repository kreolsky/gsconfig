/**
 * Сворачивает древовидную структуры в строку конфига, которая разворачивается в валидный JSON документ.
 * Каждый новый блок на новой строке. Если нужно создать список, каждый элемент списка на своей строке.
 * В строке может быть не более 2х элементов. Первый элемент ключ, второй - значение.

 * @param {2D array} array
 * Диапазон который заполнен древовидной структурой
 * @param {array} source
 * Столбец справочника содержащий искомые значения
 * @param {array} destination
 * Столбец справочника содержащий значения для подстановки
 * @return {string}
 * @customfunction
 */
function treeToConfig(arrays, br) {
  var br = br || ''
  var out = ''
  var data
  var line
  var lineLevel
  var upperLineLevel
  var lowerLineLevel
  var upperOpenSep
  var lowerCloseSep
  var lineCloseSep

  for (var i = 0; i < arrays.length; i++) {

    line = arrays[i]
    data = purgeArray(line)

    lineLevel = getLineLevel(line)
    upperLineLevel = getUpperLineLevel(arrays, i)
    lowerLineLevel = getLowerLineLevel(arrays, i)
    upperOpenSep = checkUpperNoSep(arrays, i)
    lowerCloseSep = checkLowerNoSep(arrays, i)
    lineCloseSep = checkCurrentNoSep(data)

    // Если выше родитель (высокоуровневый элемент), то указываем вложение
    if (lineLevel > upperLineLevel) {
      out += ' = {'
    }

    // Если выше одноранговый и он не открывающая скобка и в текущей строке не закрывающая скобка, то разделяем запятой
    else if (lineLevel == upperLineLevel & upperOpenSep & lineCloseSep) {
      out += ', '
    }

    // Строка из одного элемента
    if (data.length == 1) {
      out += String(data)
    }

    // Строка из двух элементов
    else if (data.length == 2) {
      out += data.join(' = ')
    }

    // Строка из трёх и более элементов
    else if (data.length > 2) {
      out += "{" + data.join(', ') + "}"
    }


    // Закрываем столько скобок, сколько уровней вложения разница со следующим элементом
    out += '}'.repeat(Math.max(0, lineLevel - lowerLineLevel))

    // Если ниже есть более высокоуровневый элемент и он не закрывающая скобка, то надо отделить запятой
    if (lineLevel > lowerLineLevel & lowerCloseSep) {
      out += ', '
    }

  }

  // Обрамляющие скобки
  if (br != '') {
    out = br[0] + out + br[1]
  }

  return out
}

function checkCurrentNoSep(line) {
  if (line.length == 1) {
    if (line[0] == "}") {
      return false
    }
  }
  return true
}

function checkLowerNoSep(arrays, row) {
  var line
  for (var i = row + 1; i < arrays.length ; i++) {
    if (any(arrays[i])) {
      line = purgeArray(arrays[i])
      if (line.length == 1 & line[0].toString().slice(-1) == "}") {
        return false
      }
      return true
    }
  }
  // Если строка последняя, то считаем её еще и закрывающей скобкой.
  // Разделение запятой не требуется
  return false
}

function checkUpperNoSep(arrays, row) {
  var line
  for (var i = row - 1; i >= 0 ; i--) {
    if (any(arrays[i])) {
      line = purgeArray(arrays[i])
      if (line.length == 1 & line[0] == "{") {
        return false
      }
      return true
    }
  }
  // Если строка первая то считаем что она же и открывающая скобка.
  // Разделение запятой не требуется
  return false
}


function getUpperLineLevel(arrays, row) {
  for (var i = row - 1; i >= 0 ; i--) {
    if (any(arrays[i])) {
      return getLineLevel(arrays[i])
    }
  }
}

function getLowerLineLevel(arrays, row) {
  for (var i = row + 1; i < arrays.length ; i++) {
    if (any(arrays[i])) {
      return getLineLevel(arrays[i])
    }
  }
  // Вернуть 1 если это последняя строка. Требуется для коректного числа закрывающих скобок
  return 1
}

function getLineLevel(line) {
  for (var i = 0; i < line.length; i++) {
    if (any(line[i])) {
      return i + 1
    }
  }
  return -1
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
 * true – если хотя бы один элемент не пустой
 *
 * @param {array} Массив для проверки.
 * Массив элементов для проверки
 */
function any(iterable) {
  if (!iterable.map) {
    return isNotEmpty(iterable)
  }

  iterable = reduceOneLineArray(iterable)
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

  iterable = reduceOneLineArray(iterable)
  return iterable.every(isNotEmpty)
}

function isNotEmpty(item) {
  return item.toString().length > 0
}
