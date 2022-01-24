window.puzzle_utils = {};

puzzle_utils.findFreeCell = function(board) {
  return board.indexOf(null);
}

/**
 * Returns list of positions reachable from srcpos  
 */
puzzle_utils.getDirections = function (board, size, srcpos) {
  let nbours = [];

  let r = Math.floor(srcpos / size);
  let c = srcpos % size;

  function pos(r, c) {
    return r * size + c;
  }

  if (r > 0) {
    nbours.push(pos(r - 1, c));
  }
  if (r < size - 1) {
    nbours.push(pos(r + 1, c));
  }
  if (c > 0) {
    nbours.push(pos(r, c - 1));
  }
  if (c < size - 1) {
    nbours.push(pos(r, c + 1));
  }

  return nbours;
};

/**
 * Checks if the move is valid
 */
puzzle_utils.validateMove = function (board, size, dst, src) {
  if (board[dst] !== null) {
    return false;
  }
  return puzzle_utils.getDirections(board, size, src).includes(dst);
};

/**
 * Returns new board with cell moved from src to dst
 */
puzzle_utils.moveCell = function (board, dst, src) {
  let newboard = board.map((v, i) => {
    if (i == src) return null;
    if (i == dst) return board[src];
    return board[i];
  });
  return newboard;
};

/**
 * Returns array of booleans for each cell indicating if its on their right place
 */
puzzle_utils.validateBoard = function (board) {
  let valid = board.map((v, i) => v == i + 1); 
  valid[board.length-1] = board[board.length-1] == null;
  return valid;
};
