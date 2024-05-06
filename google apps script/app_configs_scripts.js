/**
 * Склеивает всё содержимое блока через разделители. Внутри одной строки – внутренний разделитель,
 * если блок из нескольких строк, то они склеиваются через внешний разделитель.
 * Данные начала блока указываются из вне. Блок – расстояние от одной запоненной строки до другой. Каждая заполненная строка – отдельный блок.
 *
 * @param {string} sep_int Разделитель через который склеиваются данные внутри строки
 * @param {string} sep_block Разделитель через который склеиваются разные строки блока
 * @param {array} data Массив с данными которые нужно склеивать
 * @param {array} block_info Донор информации для разделения блоков. Блоком считается расстояние между записями в столбце.
 * Например, если донором взять столбец с ключамии, то блоком будет содержимое строк от одного ключа (включая), до другого (не включая)
 * @param {string} block_function Тип функции разбиения на блоки block, blockplus, line, lineplus (по умолчанию).
 * line - Блок – каждая заполненную строку и только заполненная строка. Расстояние между строками не попадает в блок.
 * lineplus - Блок начинается от одной запоненной строки до другой, не включая. Пустоты между строками относятся к вышестоящему блоку.
 * block - Блок начинается от одной записи и до следующей не включая. Несколько записей подряд считаются одним блоком.
 * blockplus - Блок начинается от одной группы записей и до следующей, не включая. Несколько записей подряд считаются одним блоком, пустоты между блоками относятся к вышестоящему блоку.
 * @param {string} wrapper Враппер обрамляющий результат. Формат "prefix %% suffix", где %% результирующая строка. Важно! wrapper должен содержать "%%". Значение по умолчанию - "".
 * @return {array} Массив строк соответствующих блокам.
 * @customfunction
 */
function joinStringsBlock(sep_int, sep_block, data, block_info, block_function, wrapper = "") {
  const [prefix, suffix] = wrapper.includes("%%") ? wrapper.split("%%") : ["", ""];
  const intervals = blockFunctions[block_function || "lineplus"](block_info);
  const out = new Array(data.length).fill(""); 

  intervals.forEach((start, index) => {
    if (index % 2 === 0) {
      const result = data.slice(start, intervals[index + 1])
        .map(line => line.filter(isNotEmpty).join(sep_int))
        .filter(Boolean)
        .join(sep_block);
      if (result) out[start] = prefix + result + suffix;
    }
  });
  
  return out;
}

/**
 * Склеивание данных с заголовкам в формате headers[0] = data[0][0], headers[1] = data[0][1], headers[2] = data[0][2] | headers[1] = data[1][0], ...
 * ВАЖНО! В массиве с названиями должно быть хота бы 2 элемента.
 * Автоматически откусывает # от начала заголовков и _tmp от конца в именах.
 *
 * @param {array} headers Строка с заголовками данных.
 * @param {array} data Массив с данным под заголовками.
 * @param {string} wrapper Враппер обрамляющий результат. Формат "prefix %% suffix", где %% результирующая строка. Важно! wrapper должен содержать "%%". Значение по умолчанию - "" (пустая строка).
 * @param {bool} skip_empty Флаг указывает пропускать или нет ячейки для которых нет данных. Если false, то заголовки будут с указанием пустых данных. Значение по умолчанию - "false"
 * @return {string} Данные склеены в одну строку.
 * @customfunction
 */
function toConfig(headers, data, wrapper = "", skip_empty=false) {
  const [prefix, suffix] = wrapper.includes("%%") ? wrapper.split("%%") : ["", ""];
  const sep_int = ", ";  // Разделитель данных внутри блока
  const sep_block = " | ";  // Разделитель блоков
  const sep_string = " = ";  // Разделитель внутри строки

  const result = data
      .filter(row => any(row)) // Только для ячеек где заполнена хотя бы одна
      .map(row => row.map((cell, j) => {
          const header = purgeName(headers[0][j]);
          return (!isNotEmpty(cell) & skip_empty) ? "" : header + sep_string + cell; // If cell is empty, return empty string
        })
        .filter(cell => isNotEmpty(cell))
        .join(sep_int))
      .join(sep_block);  

  return prefix + result + suffix;
}

/**
 * Расширение функции toConfig. Склеивает блоки с информацией в строки конфига. Разделение на блоки задается отдельно.
 * 
 * @param {array} headers Строка с заголовками данных.
 * @param {array} data Массив с данными под заголовками.
 * @param {array} block_info Донор информации для разделения блоков.
 * @param {string} block_function Тип функции разбиения на блоки line, lineplus, block, blockplus (по умолчанию).
 * line - Блок – каждая заполненную строку и только заполненная строка. Расстояние между строками не попадает в блок.
 * lineplus - Блок начинается от одной запоненной строки до другой, не включая. Пустоты между строками относятся к вышестоящему блоку.
 * block - Блок начинается от одной записи и до следующей не включая. Несколько записей подряд считаются одним блоком.
 * blockplus - Блок начинается от одной группы записей и до следующей, не включая. Несколько записей подряд считаются одним блоком, пустоты между блоками относятся к вышестоящему блоку.
 * @param {string} wrapper Враппер обрамляющий результат. Формат "prefix %% suffix", где %% результирующая строка. Важно! wrapper должен содержать "%%". Значение по умолчанию - "" (пустая строка).
 * @param {bool} skip_empty Флаг указывает пропускать или нет ячейки для которых нет данных. Если false, то заголовки будут с указанием пустых данных. Значение по умолчанию - "false"
 * @return {array} Массив строк соответствующих блокам.
 * @customfunction
 */
function toConfigBlock(headers, data, block_info, block_function, wrapper = "", skip_empty=false) {
  const intervals = blockFunctions[block_function || "blockplus"](block_info);
  const result = new Array(data.length).fill(""); // Предварительное заполнение массива пустыми строками

  intervals.forEach((start, index) => {
    if (index % 2 === 0) { // Проверяем, что index - четный, то есть start блока
      result[start] = toConfig(headers, data.slice(start, intervals[index + 1]), wrapper, skip_empty);
    }
  });

  return result;
}

/**
 * Обьект выбора функции определения блока
 */

const blockFunctions = {
  line: defineOneLineBlock,
  lineplus: defineOneLineBlockPlus,
  block: defineBlock,
  blockplus: defineBlockPlus
};

/**
 * Вспомогательные функции
 */

// Удаление мусора из заголовков
function purgeName(name) {
  return name.replace(/^#/, "").replace(/_tmp$/, "");
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
    if (isNotEmpty(item)) {
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
    if (isNotEmpty(row)) {
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
  return String(item).length > 0
}
