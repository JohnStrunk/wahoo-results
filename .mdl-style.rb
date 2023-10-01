#https://github.com/markdownlint/markdownlint/blob/master/docs/RULES.md

all

rule 'MD007', :indent => 2
rule 'MD009', :br_spaces => 2
rule 'MD013', :ignore_code_blocks => true, :tables => false
rule 'MD024', :allow_different_nesting => true
exclude_rule 'MD026' # Trailing punctuation in header
#exclude_rule 'MD040' # Fenced code blocks should have a language specified
rule 'MD046', :style => :fenced
