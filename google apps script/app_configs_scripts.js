/**
 * Возвращает true, если хотя бы один элемент массива истинный.
 *
 * @param {array} iterable - Массив элементов для проверки.
 */
function any(iterable) {
  // Проверяем, является ли объект массивом
  if (!Array.isArray(iterable)) {
    // Для не массивов просто проверяем "истинность" самого объекта
    return !!iterable;
  }

  // Возвращает true, если хотя бы один элемент массива "истинный"
  return iterable.some(item => !!item);
}

/**
 * Возвращает true, если все элементы массива истинные.
 *
 * @param {array} iterable - Массив элементов для проверки.
 */
function all(iterable) {
  // Проверяем, является ли объект массивом
  if (!Array.isArray(iterable)) {
    // Для не массивов просто проверяем "истинность" самого объекта
    return !!iterable;
  }

  // Возвращает true, если все элементы массива "истинные"
  return iterable.every(item => !!item);
}

/**
 * Проверяет, не пуст ли элемент.
 *
 * @param {*} item - Элемент для проверки.
 */
function isNotEmpty(item) {
  return item !== undefined && item !== null && item !== '';
}

/**
 * Склеивает всё содержимое блока через разделители. Внутри одной строки – внутренний разделитель,
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
  br = br || "";
  var out = new Array(data.length); // Инициализируем выходной массив с таким же количеством элементов, как в data
  
  var intervals = defineOneLineBlockPlus(block_info);

  for (var i = 0; i < intervals.length; i += 2) {
    var blockData = [];
    
    // Собираем данные блока, используя функцию isNotEmpty для проверки
    for (var j = intervals[i]; j < intervals[i + 1]; j++) {
      var line = data[j].filter(isNotEmpty);
      if (line.length > 0) {
        blockData.push(line.join(sepInt));
      }
    }

    // Склеиваем данные блока и добавляем обрамляющие скобки, если блок не пустой
    if (blockData.length > 0) {
      var blockString = blockData.join(sepExt);
      if (br.length > 1) {
        blockString = br[0] + blockString + br[1];
      }
      out[intervals[i]] = blockString; // Записываем результат в позицию начала блока
    }
  }
  
  return out;
}

function purgeName(string) {
  // Удаление "#" с начала строки, если присутствует
  if (string.startsWith("#")) {
    string = string.slice(1);
  }

  // Удаление "_tmp" с конца строки, если присутствует
  if (string.endsWith("_tmp")) {
    string = string.slice(0, -4);
  }

  return string;
}

// Определяет расстояние между записями в столбце. Блок начинается от одной записи и до следующей не включая. Несколько записей подряд считаются одним блоком.
function defineBlock(data) {
  let new_block = true;
  let out = [];

  data.forEach((row, i) => {
    if (!isNotEmpty(row[0]) && !new_block) {
      new_block = true;  // Начало нового блока
      out.push(i);  // Конец предыдущего блока
    } else if (isNotEmpty(row[0]) && new_block) {
      new_block = false;  // Текущая непустая строка является частью текущего блока
      out.push(i);  // Начало текущего блока
    }
  });

  // Добавляем конец последнего блока, если он не был добавлен
  if (!new_block) {
    out.push(data.length);
  }

  return out;
}

// Блок начинается от одной группы записей и до следующей, не включая. Пустоты между блоками относятся к вышестоящему блоку.
function defineBlockPlus(data) {
  var new_block = true; // Флаг, показывающий, что мы в начале нового блока
  var out = []; // Выходной массив для хранения индексов начала и конца блоков

  // Перебираем все строки данных
  data.forEach((item, i) => {
    if (isNotEmpty(item[0])) {
      // Если строка непустая и мы находимся в начале нового блока
      if (new_block) {
        // Если это не самый первый блок, добавляем индекс как конец предыдущего блока
        if (out.length > 0) out.push(i);
        // Добавляем индекс как начало текущего блока
        out.push(i);
        // Сбрасываем флаг нового блока, так как мы только что начали блок
        new_block = false;
      }
    } else {
      // Если строка пустая, устанавливаем флаг нового блока
      new_block = true;
    }
  });

  out.push(data.length);
  return out;
}

// Блок – каждая заполненнаю строку и только заполненная строка.
// ВАЖНО! Расстояние между строками не попадает в блок!
function defineOneLineBlock(data) {
  var out = [];

  data.forEach(function(row, index) {
    if (all(row)) {
      out.push(index); // Начало блока - индекс заполненной строки
      out.push(index + 1); // Конец блока - индекс следующей строки
    }
  });

  return out;
}

// Блок начинается от одной запоненной строки до другой, не включая. Пустые строки между блоками относятся к вышестоящему блоку.
function defineOneLineBlockPlus(data) {
  var out = [];
  var flag = false; // Флаг первого элемента последовательности

  data.forEach(function(row, index) {
    if (all(row)) {
      out.push(index); // Индекс начала первого блока и конец блока для всех остальных
      if (flag) {
        out.push(index); // Индекс начала второго и всех последующих блоков
      }
      flag = true; // Установка флага после обнаружения первого непустого блока
    }
  });

  out.push(data.length); // Индекс конца последнего блока
  return out;
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
  br = br || "";
  var txt = br[0] || "";
  var txt_end = br.slice(-1) || "";

  var sepInt = ", ";  // Разделитель данных внутри блока
  var sepBlock = " | ";  // Разделитель блоков
  var sepString = " = ";  // Разделитель внутри строки

  // Откусывает префикс "@" и суффикс "_tmp", если они есть
  names_array = names_array[0].map(purgeName);

  data_array.forEach((row, i) => {
    if (any(row)) {
      // Создаем строку конфигурации для текущей строки
      var lineConfig = row.map((cell, j) => names_array[j] + sepString + cell).join(sepInt);
      // Добавляем к общей строке, с разделителем блоков если это не первая строка
      txt += (i > 0 ? sepBlock : "") + lineConfig;
    }
  });

  // Если после прохода по всем строкам txt не изменился, возвращаем пустую строку
  return txt === br[0] ? "" : txt + txt_end;
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
function toConfigBlock(headers, block_info, data, block_function = "blockplus", br = "") {
  const blockFunctions = {
    line: defineOneLineBlock,
    lineplus: defineOneLineBlockPlus,
    block: defineBlock,
    blockplus: defineBlockPlus
  };

  const intervals = blockFunctions[block_function](block_info);
  const out = new Array(data.length).fill(""); // Предварительное заполнение массива пустыми строками

  intervals.forEach((start, index) => {
    if (index % 2 === 0) { // Проверяем, что index - четный, то есть start блока
      const end = intervals[index + 1];
      out[start] = toConfig(headers, data.slice(start, end), br);
    }
  });

  return out;
}