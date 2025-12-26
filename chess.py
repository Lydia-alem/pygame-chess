import pygame
import sys

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 600, 700
BOARD_SIZE = 8
SQUARE_SIZE = WIDTH // BOARD_SIZE
FPS = 60

# Colors
LIGHT_BROWN = (240, 217, 181)
DARK_BROWN = (181, 136, 99)
HIGHLIGHT = (255, 255, 0, 128)
VALID_MOVE = (0, 255, 0, 128)
LAST_MOVE = (173, 216, 230, 128)  # Light blue for last move

class Piece:
    def __init__(self, type, color, row, col):
        self.type = type
        self.color = color
        self.row = row
        self.col = col
        self.has_moved = False
        
    def __str__(self):
        return f"{self.color}{self.type}"
    
    def copy(self):
        p = Piece(self.type, self.color, self.row, self.col)
        p.has_moved = self.has_moved
        return p

class ChessGame:
    def __init__(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.current_player = 'w'
        self.selected_piece = None
        self.valid_moves = []
        self.last_move = None
        self.check = False
        self.checkmate = False
        self.move_history = []
        self.setup_board()
        
    def setup_board(self):
        pieces_order = ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']
        for col in range(8):
            self.board[0][col] = Piece(pieces_order[col], 'b', 0, col)
            self.board[1][col] = Piece('p', 'b', 1, col)
            self.board[7][col] = Piece(pieces_order[col], 'w', 7, col)
            self.board[6][col] = Piece('p', 'w', 6, col)
    
    def draw_board(self, screen):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                color = LIGHT_BROWN if (row + col) % 2 == 0 else DARK_BROWN
                pygame.draw.rect(screen, color, 
                                 (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                                  SQUARE_SIZE, SQUARE_SIZE))
    
    def draw_pieces(self, screen, piece_images):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece:
                    piece_key = str(piece)
                    if piece_key in piece_images:
                        img = piece_images[piece_key]
                        screen.blit(img, (col * SQUARE_SIZE, row * SQUARE_SIZE))
    
    def draw_highlights(self, screen):
        if self.last_move:
            from_row, from_col, to_row, to_col = self.last_move
            for pos in [(from_row, from_col), (to_row, to_col)]:
                row, col = pos
                highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                highlight_surface.fill(LAST_MOVE)
                screen.blit(highlight_surface, (col * SQUARE_SIZE, row * SQUARE_SIZE))
        
        if self.selected_piece:
            row, col = self.selected_piece.row, self.selected_piece.col
            highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight_surface.fill(HIGHLIGHT)
            screen.blit(highlight_surface, (col * SQUARE_SIZE, row * SQUARE_SIZE))
            for move in self.valid_moves:
                target_row, target_col = move
                pygame.draw.circle(screen, (0, 200, 0), 
                                   (target_col * SQUARE_SIZE + SQUARE_SIZE//2,
                                    target_row * SQUARE_SIZE + SQUARE_SIZE//2),
                                   SQUARE_SIZE//6)
    
    def get_piece_at(self, row, col):
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None
    
    def select_piece(self, row, col):
        piece = self.get_piece_at(row, col)
        if piece and piece.color == self.current_player:
            self.selected_piece = piece
            self.valid_moves = self.get_valid_moves(piece)
            return True
        return False
    
    def move_piece(self, from_row, from_col, to_row, to_col):
        piece = self.get_piece_at(from_row, from_col)
        if not piece:
            return False
            
        if (to_row, to_col) in self.get_valid_moves(piece):
            move_record = {
                'piece': piece.copy(),
                'from': (from_row, from_col),
                'to': (to_row, to_col),
                'captured': self.get_piece_at(to_row, to_col)
            }
            
            captured = self.board[to_row][to_col]
            self.board[to_row][to_col] = piece
            self.board[from_row][from_col] = None
            piece.row, piece.col = to_row, to_col
            piece.has_moved = True
            
            if piece.type == 'p':
                if (piece.color == 'w' and to_row == 0) or (piece.color == 'b' and to_row == 7):
                    piece.type = 'q'
            
            self.last_move = (from_row, from_col, to_row, to_col)
            self.move_history.append(move_record)
            
            self.current_player = 'b' if self.current_player == 'w' else 'w'
            
            self.check = self.is_in_check(self.current_player)
            if self.check:
                if self.is_checkmate(self.current_player):
                    self.checkmate = True
            
            self.selected_piece = None
            self.valid_moves = []
            return True
        return False
    
    # --- Move generation functions ---
    
    def get_valid_moves(self, piece):
        moves = self.get_piece_moves_without_check(piece)
        valid_moves = []
        for move in moves:
            if not self.move_causes_check(piece, move[0], move[1]):
                valid_moves.append(move)
        return valid_moves
    
    def get_piece_moves_without_check(self, piece):
        if piece.type == 'p':
            return self.get_pawn_moves(piece)
        elif piece.type == 'r':
            return self.get_rook_moves(piece)
        elif piece.type == 'n':
            return self.get_knight_moves(piece)
        elif piece.type == 'b':
            return self.get_bishop_moves(piece)
        elif piece.type == 'q':
            return self.get_queen_moves(piece)
        elif piece.type == 'k':
            return self.get_king_moves(piece, check_castling=False)
        return []
    
    def get_pawn_moves(self, pawn):
        moves = []
        direction = -1 if pawn.color == 'w' else 1
        start_row = 6 if pawn.color == 'w' else 1
        
        # Move forward
        if self.get_piece_at(pawn.row + direction, pawn.col) is None:
            moves.append((pawn.row + direction, pawn.col))
            if pawn.row == start_row and self.get_piece_at(pawn.row + 2 * direction, pawn.col) is None:
                moves.append((pawn.row + 2 * direction, pawn.col))
        
        # Captures
        for dc in [-1, 1]:
            target_col = pawn.col + dc
            target_row = pawn.row + direction
            target_piece = self.get_piece_at(target_row, target_col)
            if target_piece and target_piece.color != pawn.color:
                moves.append((target_row, target_col))
        
        return moves
    
    def get_rook_moves(self, rook):
        moves = []
        directions = [(1,0), (-1,0), (0,1), (0,-1)]
        for dr, dc in directions:
            for i in range(1,8):
                r = rook.row + dr*i
                c = rook.col + dc*i
                if not (0 <= r < 8 and 0 <= c < 8):
                    break
                target = self.get_piece_at(r, c)
                if target is None:
                    moves.append((r,c))
                elif target.color != rook.color:
                    moves.append((r,c))
                    break
                else:
                    break
        return moves
    
    def get_knight_moves(self, knight):
        moves = []
        offsets = [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]
        for dr, dc in offsets:
            r = knight.row + dr
            c = knight.col + dc
            if 0<=r<8 and 0<=c<8:
                target = self.get_piece_at(r,c)
                if target is None or target.color != knight.color:
                    moves.append((r,c))
        return moves
    
    def get_bishop_moves(self, bishop):
        moves = []
        directions = [(1,1),(1,-1),(-1,1),(-1,-1)]
        for dr, dc in directions:
            for i in range(1,8):
                r = bishop.row + dr*i
                c = bishop.col + dc*i
                if not (0<=r<8 and 0<=c<8):
                    break
                target = self.get_piece_at(r,c)
                if target is None:
                    moves.append((r,c))
                elif target.color != bishop.color:
                    moves.append((r,c))
                    break
                else:
                    break
        return moves
    
    def get_queen_moves(self, queen):
        return self.get_rook_moves(queen) + self.get_bishop_moves(queen)
    
    def get_king_moves(self, king, check_castling=True):
        moves = []
        directions = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
        for dr, dc in directions:
            r = king.row + dr
            c = king.col + dc
            if 0<=r<8 and 0<=c<8:
                target = self.get_piece_at(r,c)
                if target is None or target.color != king.color:
                    moves.append((r,c))
        if check_castling and not king.has_moved and not self.is_in_check(king.color):
            # Kingside
            rook = self.get_piece_at(king.row, 7)
            if rook and rook.type=='r' and not rook.has_moved:
                if self.get_piece_at(king.row,5) is None and self.get_piece_at(king.row,6) is None:
                    if not self.square_under_attack(king.row,5,king.color) and not self.square_under_attack(king.row,6,king.color):
                        moves.append((king.row,6))
            # Queenside
            rook = self.get_piece_at(king.row, 0)
            if rook and rook.type=='r' and not rook.has_moved:
                if self.get_piece_at(king.row,1) is None and self.get_piece_at(king.row,2) is None and self.get_piece_at(king.row,3) is None:
                    if not self.square_under_attack(king.row,2,king.color) and not self.square_under_attack(king.row,3,king.color):
                        moves.append((king.row,2))
        return moves
    
    # --- Check functions ---
    
    def square_under_attack(self, row, col, defending_color):
        attacking_color = 'b' if defending_color=='w' else 'w'
        for r in range(8):
            for c in range(8):
                piece = self.get_piece_at(r,c)
                if piece and piece.color==attacking_color:
                    moves = self.get_piece_moves_without_check(piece)
                    if (row,col) in moves:
                        return True
        return False
    
    def is_in_check(self, color):
        king_pos = None
        for r in range(8):
            for c in range(8):
                p = self.get_piece_at(r,c)
                if p and p.type=='k' and p.color==color:
                    king_pos=(r,c)
                    break
            if king_pos: break
        if not king_pos: return False
        return self.square_under_attack(king_pos[0], king_pos[1], color)
    
    def move_causes_check(self, piece, to_row, to_col):
        original_piece = self.get_piece_at(to_row, to_col)
        original_row, original_col = piece.row, piece.col
        self.board[to_row][to_col] = piece
        self.board[original_row][original_col] = None
        piece.row, piece.col = to_row, to_col
        in_check = self.is_in_check(piece.color)
        self.board[original_row][original_col] = piece
        self.board[to_row][to_col] = original_piece
        piece.row, piece.col = original_row, original_col
        return in_check
    
    def is_checkmate(self, color):
        for r in range(8):
            for c in range(8):
                p = self.get_piece_at(r,c)
                if p and p.color==color:
                    if self.get_valid_moves(p):
                        return False
        return True

# --- Drawing & utilities ---

def load_piece_images():
    piece_images = {}
    font = pygame.font.SysFont('segoeuisymbol', SQUARE_SIZE-20)
    symbols = {
        'wr':'♜','wn':'♞','wb':'♝','wq':'♛','wk':'♚','wp':'♟',
        'br':'♖','bn':'♘','bb':'♗','bq':'♕','bk':'♔','bp':'♙'
    }
    for key, symbol in symbols.items():
        color = (255,255,255) if key[0]=='w' else (50,50,50)
        text_surface = font.render(symbol, True, color)
        image = pygame.Surface((SQUARE_SIZE,SQUARE_SIZE),pygame.SRCALPHA)
        rect = text_surface.get_rect(center=(SQUARE_SIZE//2,SQUARE_SIZE//2))
        image.blit(text_surface, rect)
        piece_images[key] = image
    return piece_images

def draw_game_status(screen, game):
    font = pygame.font.SysFont(None,36)
    player_color = "White" if game.current_player=='w' else "Black"
    player_text = font.render(f"{player_color}'s Turn", True,(255,255,255))
    pygame.draw.rect(screen,(50,50,50),(WIDTH-150,10,140,40))
    screen.blit(player_text,(WIDTH-140,15))
    
    if game.checkmate:
        status_color=(220,20,60)
        status_text="CHECKMATE!"
        winner="White" if game.current_player=='b' else "Black"
        sub_text=f"{winner} wins!"
    elif game.check:
        status_color=(220,20,60)
        status_text="CHECK!"
        sub_text=""
    else:
        status_color=(60,179,113)
        status_text="Normal"
        sub_text=""
    pygame.draw.rect(screen,status_color,(10,10,180,60))
    status_font = pygame.font.SysFont(None,28)
    screen.blit(status_font.render(status_text,True,(255,255,255)),(20,20))
    if sub_text:
        screen.blit(status_font.render(sub_text,True,(255,255,255)),(20,45))

# --- Main loop ---

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess Game")
    clock = pygame.time.Clock()
    
    game = ChessGame()
    piece_images = load_piece_images()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running=False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button==1:
                    x,y = event.pos
                    col = x//SQUARE_SIZE
                    row = y//SQUARE_SIZE
                    if game.selected_piece:
                        if game.move_piece(game.selected_piece.row, game.selected_piece.col,row,col):
                            pass
                        elif game.select_piece(row,col):
                            pass
                        else:
                            game.selected_piece=None
                            game.valid_moves=[]
                    else:
                        game.select_piece(row,col)
            elif event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    running=False
                elif event.key==pygame.K_r:
                    game=ChessGame()
                elif event.key==pygame.K_u:
                    if game.move_history:
                        last_move=game.move_history.pop()
                        piece=last_move['piece']
                        from_pos=last_move['from']
                        captured=last_move['captured']
                        game.board[from_pos[0]][from_pos[1]]=piece
                        piece.row,piece.col=from_pos
                        to_pos=last_move['to']
                        game.board[to_pos[0]][to_pos[1]]=captured
                        game.current_player='w' if game.current_player=='b' else 'w'
                        game.selected_piece=None
                        game.valid_moves=[]
                        game.check=False
                        game.checkmate=False
                        game.last_move=None
        
        screen.fill((40,40,40))
        game.draw_board(screen)
        game.draw_highlights(screen)
        game.draw_pieces(screen, piece_images)
        draw_game_status(screen, game)
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__=="__main__":
    main()
