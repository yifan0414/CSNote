# 0 What I learned and useful
- C 语言的内存管理初体验
- 与 CS61B sp21 project1 的队列对比
- 命令行循环测试的设计 `./qtest` 函数 #todo 

# 1 Introduce

这是 csapp 的 Lab0，定位只是一个编程能力测试，按照 professor 的原话就是如果你做这个实验超过 5 hours，那么你应该考虑下先去提升下 C 语言的水平。

其实这个 Lab 的 task 还是比较清晰的，就是使用 C 语言实现一个队列，代码的 skeleton 已经给出了，需要我们完成以下函数。

1. **queue_new**: Create a new, empty queue. queue_free: Free all storage used by a queue.

2. **queue_free**: Free all storage used by a queue.

3. **queue_insert_head**: Attempt to insert a new element at the head of the queue (`LIFO` discipline). queue_insert_tail: Attempt to insert a new element at the tail of the queue (`FIFO` discipline).

4. **queue_insert_tail**: Attempt to insert a new element at the tail of the queue (FIFO discipline).

5. **queue_remove_head**: Attempt to remove the element at the head of the queue. queue_size: Compute the number of elements in the queue.

6. **queue_size**: Compute the number of elements in the queue.

5. **queue_reverse**: Reorder the list so that the queue elements are reversed in order. This function should not allocate or free any list elements (either directly or via calls to other functions that allocate or free list elements.) Instead, it should rearrange the existing elements.

# 2 Note

相较于 JAVA，我们必须手动进行内存管理，包括内存申请与内存释放。这里非常繁琐，因为考虑到不仅仅是 `list_ele_t` 需要内存申请，其中的 `value` 指向的 `char*` 也需要内存申请，后面的申请不成功需要把前面申请的内存释放掉。这里我们以 `queue_insert_head` 为例进行说明。

```cpp
/**
 * @brief Attempts to insert an element at head of a queue
 *
 * This function explicitly allocates space to create a copy of `s`.
 * The inserted element points to a copy of `s`, instead of `s` itself.
 *
 * @param[in] q The queue to insert into
 * @param[in] s String to be copied and inserted into the queue
 *
 * @return true if insertion was successful
 * @return false if q is NULL, or memory allocation failed
 */
bool queue_insert_head(queue_t *q, const char *s) {
    if (q == NULL)
        return false;
    list_ele_t *newh;
    /* TODO: What should you do if the q is NULL? */
    newh = malloc(sizeof(list_ele_t));
    if (newh == NULL)
        return false;
    /* Don't forget to allocate space for the string and copy it */
    char *scopy = malloc(sizeof(char) * (strlen(s) + 1));
    /* What if either call to malloc returns NULL? */
    if (scopy == NULL) {
        free(newh); // **重要**，如果不释放会造成内存泄露
        return false;
    }
    newh->next = q->head;
    strcpy(scopy, s);
    scopy[strlen(s)] = '\0'
    newh->value = scopy;
    if (q->head == NULL) {
        q->tail = newh;
    }
    q->head = newh;
    q->size++;
    return true;
}
```


[[cprogramminglab.pdf#page=1&offset=70.56,283.153|Overview]]


不错的选择 [[cprogramminglab.pdf#page=2&selection=124,0,129,23]]