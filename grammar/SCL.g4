grammar SCL;

functionBlock
    : FUNCTION_BLOCK IDENT
      blockHeader*
      (varSection | constantSection)*
      BEGIN
      statementList
      END_FUNCTION_BLOCK
    ;

blockHeader
    : IDENT (COLON | EQ) (literal | IDENT)
    ;

constantSection
    : CONST constDecl* END_CONST
    ;

constDecl
    : IDENT (COLON typeName)? ASSIGN expression SEMI
    ;

varSection
    : varSectionHeader varDecl* END_VAR
    ;

varSectionHeader
    : VAR_INPUT
    | VAR_OUTPUT
    | VAR_IN_OUT
    | VAR
    | VAR_TEMP
    | VAR_CONSTANT
    ;

varDecl
    : IDENT (AT IDENT)? COLON typeName (ASSIGN expression)? SEMI
    ;

typeName
    : IDENT
    | ARRAY LBRACKET indexRange (COMMA indexRange)* RBRACKET OF typeName
    | STRUCT varDecl* END_STRUCT
    ;

indexRange
    : expression RANGE expression
    ;

statementList
    : (statement)*
    ;

statement
    : assignment SEMI
    | ifStatement SEMI
    | forStatement SEMI
    | whileStatement SEMI
    | repeatStatement SEMI
    | caseStatement SEMI
    | callStatement SEMI
    | returnStatement SEMI
    | exitStatement SEMI
    | SEMI // empty statement
    ;

assignment
    : expression ASSIGN expression
    ;

ifStatement
    : IF expression THEN statementList
      elsifBranch*
      elseBranch?
      END_IF
    ;

elsifBranch
    : ELSIF expression THEN statementList
    ;

elseBranch
    : ELSE statementList
    ;

forStatement
    : FOR IDENT ASSIGN expression TO expression (BY expression)? DO statementList END_FOR
    ;

whileStatement
    : WHILE expression DO statementList END_WHILE
    ;

repeatStatement
    : REPEAT statementList UNTIL expression END_REPEAT
    ;

caseStatement
    : CASE expression OF caseBranch+ elseCaseBranch? END_CASE
    ;

caseBranch
    : caseValueList COLON statementList
    ;

caseValueList
    : caseValue (COMMA caseValue)*
    ;

caseValue
    : expression (RANGE expression)?
    ;

elseCaseBranch
    : ELSE statementList
    ;

callStatement
    : IDENT LPAREN (parameterList)? RPAREN
    ;

parameterList
    : parameter (COMMA parameter)*
    ;

parameter
    : (IDENT ASSIGN )? expression
    | IDENT DARROW expression
    ;

returnStatement
    : RETURN
    ;

exitStatement
    : EXIT
    ;

expressionList
    : expression (COMMA expression)*
    ;

// Expressions with precedence (top-most has highest precedence)
expression
    : LPAREN expression RPAREN                              # ParenExpr
    | expression LBRACKET expressionList RBRACKET           # IndexExpr
    | expression DOT IDENT                                  # MemberExpr
    | NOT expression                                        # NotExpr
    | MINUS expression                                      # NegExpr
    | PLUS expression                                       # PosExpr
    | expression (STAR | SLASH | MOD) expression            # MulDivModExpr
    | expression (PLUS | MINUS) expression                  # AddSubExpr
    | expression (EQ | NE | LT | LE | GT | GE) expression    # CompExpr
    | expression AND expression                             # AndExpr
    | expression (OR | XOR) expression                       # OrExpr
    | literal                                               # LiteralExpr
    | IDENT                                                 # IdentExpr
    | callStatement                                         # CallExpr
    ;

literal
    : INT_LIT
    | REAL_LIT
    | BOOL_LIT
    | STRING_LIT
    | HEX_LIT
    | TIME_LIT
    ;

// Lexer rules for symbols
COLON : ':' ;
ASSIGN : ':=' ;
SEMI : ';' ;
COMMA : ',' ;
RANGE : '..' ;
LPAREN : '(' ;
RPAREN : ')' ;
LBRACKET : '[' ;
RBRACKET : ']' ;
DOT : '.' ;
EQ : '=' ;
NE : '<>' ;
LT : '<' ;
LE : '<=' ;
GT : '>' ;
GE : '>=' ;
PLUS : '+' ;
MINUS : '-' ;
STAR : '*' ;
SLASH : '/' ;
DARROW : '=>' ;

// Lexer Rules (Case-Insensitive helper fragments for keywords)
fragment A : [aA] ;
fragment B : [bB] ;
fragment C : [cC] ;
fragment D : [dD] ;
fragment E : [eE] ;
fragment F : [fF] ;
fragment G : [gG] ;
fragment H : [hH] ;
fragment I : [iI] ;
fragment J : [jJ] ;
fragment K : [kK] ;
fragment L : [lL] ;
fragment M : [mM] ;
fragment N : [nN] ;
fragment O : [oO] ;
fragment P : [pP] ;
fragment Q : [qQ] ;
fragment R : [rR] ;
fragment S : [sS] ;
fragment T : [tT] ;
fragment U : [uU] ;
fragment V : [vV] ;
fragment W : [wW] ;
fragment X : [xX] ;
fragment Y : [yY] ;
fragment Z : [zZ] ;

FUNCTION_BLOCK : F U N C T I O N '_' B L O C K ;
END_FUNCTION_BLOCK : E N D '_' F U N C T I O N '_' B L O C K ;
VAR_INPUT : V A R '_' I N P U T ;
VAR_OUTPUT : V A R '_' O U T P U T ;
VAR_IN_OUT : V A R '_' I N '_' O U T ;
VAR : V A R ;
VAR_TEMP : V A R '_' T E M P ;
VAR_CONSTANT : V A R '_' C O N S T A N T ;
END_VAR : E N D '_' V A R ;
CONST : C O N S T ;
END_CONST : E N D '_' C O N S T ;
BEGIN : B E G I N ;
IF : I F ;
THEN : T H E N ;
ELSIF : E L S I F ;
ELSE : E L S E ;
END_IF : E N D '_' I F ;
FOR : F O R ;
TO : T O ;
BY : B Y ;
DO : D O ;
END_FOR : E N D '_' F O R ;
WHILE : W H I L E ;
END_WHILE : E N D '_' W H I L E ;
REPEAT : R E P E A T ;
UNTIL : U N T I L ;
END_REPEAT : E N D '_' R E P E A T ;
CASE : C A S E ;
OF : O F ;
END_CASE : E N D '_' C A S E ;
RETURN : R E T U R N ;
EXIT : E X I T ;
AND : A N D ;
OR : O R ;
XOR : X O R ;
NOT : N O T ;
MOD : M O D ;
AT : A T ;
ARRAY : A R R A Y ;
STRUCT : S T R U C T ;
END_STRUCT : E N D '_' S T R U C T ;

BOOL_LIT
    : T R U E
    | F A L S E
    ;

IDENT
    : [a-zA-Z_] [a-zA-Z0-9_]* ('.' [a-zA-Z0-9_]+)*
    ;

INT_LIT
    : [0-9]+
    ;

REAL_LIT
    : [0-9]+ '.' [0-9]+
    ;

HEX_LIT
    : [0-9]+ '#' [0-9a-fA-F_]+
    ;

TIME_LIT
    : [tT] '#' ('-')? [a-zA-Z0-9_.]+
    ;

STRING_LIT
    : '\'' (~'\'')* '\''
    ;

WS
    : [ \t\r\n]+ -> skip
    ;

LINE_COMMENT
    : '//' ~[\r\n]* -> skip
    ;

BLOCK_COMMENT
    : '(*' .*? '*)' -> skip
    ;
