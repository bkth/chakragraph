import sys


class Node(object):

    def __init__(self, name):
        
        self.name       = name
        self.stmts      = []
        self.successors = []
        self.true_successor = []

    def add_succ(self, succ, true_or_false=True):
        self.true_successor.append(true_or_false)
        self.successors.append(succ)

    def add_stmt(self, stmt):
        self.stmts.append(stmt)

    def __str__(self):
        s = "Node %s\n" % self.name
        for stmt in self.stmts:
            s += "\t%s\n" % stmt
        for succ in self.successors:
            s += "\t\tSuccessor: %s\n" % succ.name
        return s

    def format_stmts(self):

        max_len = 0
        for stmt in self.stmts:
            parts = [x for x in stmt.split(" ") if x]
            lhs = parts[0]
            if len(lhs) > max_len:
                max_len = len(lhs)

        fmt = "%%-%ds %%s %%-6s %%s\\l" % max_len 
        ret = ""

        for stmt in self.stmts:
            if "=" not in stmt:
                ret += stmt.lstrip().replace("#", "").rstrip()
                continue
            parts = [x for x in stmt.split(" ") if x][:-1]
            ret += fmt % (parts[0], parts[1], parts[2], " ".join(parts[3:]))

        return ret

lines = None
with open(sys.argv[1], "rb") as f:
    lines = [x.rstrip().lstrip() for x in f.readlines()]

cursor = 0

# advance past FunctionEntry
while "FunctionEntry" not in lines[cursor]:
    cursor += 1
cursor +=1

node_list = []
n = Node("entry")
current_node = n
node_list.append(n)

counter = 0

def get_name():
    global counter
    counter += 1
    return "a%d" % counter

def get_node_for_label(label_name):
    for n in node_list:
        if n.name == label_name:
            return n

    # not found
    node = Node(label_name)
    node_list.append(node)
    return node


def lower_graph_to_dot(head):

    f = open("graph.dot", "wb+")
    f.write("digraph {\n")
    # DECLS
    already_decl = []
    todo = []
    #f.write('%s [label="%s" shape=box]\n' % (head.name.replace("$", ""), "\\l".join(head.stmts)))
    f.write('%s [label="%s" shape=box fontname=Consolas]\n' % (head.name.replace("$", ""), head.format_stmts()))
    already_decl.append(head)
    for succ in head.successors:
        if not succ.stmts:
            for entry in equivalent_labels:
                if succ in entry:
                    succ = entry[-1]
                    break
        todo.append(succ)

    while todo:
        n = todo.pop()
        #f.write('%s [label="%s" shape=box]\n' % (n.name.replace("$", ""), "\\l".join(n.stmts)))
        f.write('%s [label="%s" shape=box fontname=Consolas]\n' % (n.name.replace("$", ""), n.format_stmts()))
        already_decl.append(n)
        for succ in n.successors:
            if not succ.stmts:
                for entry in equivalent_labels:
                    if succ in entry:
                        succ = entry[-1]
                        break
            if succ in already_decl:
                continue
            todo.append(succ)


    # FLOW
    already_decl = []
    todo = []
    
    already_decl.append(head)
    for i, succ in enumerate(head.successors):
        if not succ.stmts:
            for entry in equivalent_labels:
                if succ in entry:
                    succ = entry[-1]
                    break
        f.write('%s -> %s [color=%s]\n' % (head.name.replace("$", ""), succ.name.replace("$", ""), "green" if head.true_successor[i] else "red"))
        todo.append(succ)

    while todo:
        n = todo.pop()
        for i, succ in enumerate(n.successors):
            if not succ.stmts:
                print("TETE")
                for entry in equivalent_labels:
                    if succ in entry:
                        succ = entry[-1]
                        break
            f.write('%s -> %s [color=%s]\n' % (n.name.replace("$", ""), succ.name.replace("$", ""), "green" if n.true_successor[i] else "red"))
        already_decl.append(n)
        for succ in n.successors:
            if succ in already_decl:
                continue
            todo.append(succ)

    f.write("}\n")
    f.flush()
    f.close()

def print_graph(head):
    already_printed = []
    todo = []
    print head
    already_printed.append(head)
    for succ in head.successors:
        todo.append(succ)

    while todo:
        n = todo.pop()
        print n
        already_printed.append(n)
        for succ in n.successors:
            if succ in already_printed:
                continue
            todo.append(succ)


equivalent_labels = []

while cursor < len(lines):
    ins = lines[cursor]
    print "Current node is %s, ins is %s" % (current_node.name, ins)
    if not ins:
        cursor += 1
        continue

    if "Line" in ins or "Col" in ins:
        cursor += 1
        continue
    # check for label
    if ins[0] == "$":
        label = ins.split(":")[0]
        print "label found alone is %s" % label 
        backup = current_node
        current_node = get_node_for_label(label)
        if normal_path_taken:
            backup.add_succ(current_node)
        cursor += 1
        if last_thing_treated_was_a_label:
            print "YOLOOOOOO"
            for entry in equivalent_labels:
                if last_added_label in entry:
                    entry.append(current_node)
                    break
        else:
            equivalent_labels.append([current_node])
        last_thing_treated_was_a_label = True
        last_added_label = current_node
        continue
    last_thing_treated_was_a_label = False
    normal_path_taken = False
    # check for control flow instruction
    if "$" in ins:
        current_node.add_stmt(ins)
        backup = current_node
        label = [x for x in ins.split(" ") if x][1]
        print "label found in jump instruction is %s" % label 
        node = get_node_for_label(label) # make sure the label target node is create
        # check if the next node has a label just in case
        if lines[cursor+1][0] == "$":
            ins2 = lines[cursor+1]
            label = ins2.split(":")[0]
            current_node = get_node_for_label(label)
        else:
            current_node = get_node_for_label(get_name())
        if "JMP" not in ins:  
            backup.add_succ(current_node, true_or_false=False)    
        backup.add_succ(node, true_or_false=True)
        cursor += 1
        continue

    normal_path_taken = True
    current_node.add_stmt(ins)
    cursor += 1

print equivalent_labels



print_graph(n)
lower_graph_to_dot(n)
