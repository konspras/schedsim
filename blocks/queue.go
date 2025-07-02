package blocks

import (
	//"container/heap"
	"container/heap"
	"container/list"
	"fmt"

	//"sort"
	"github.com/epfl-dcsl/schedsim/engine"
)

var count = 0

// Queue is a imple FIFO queue
type Queue struct {
	l  *list.List
	id int
}

// NewQueue returns a new *Queue
func NewQueue() *Queue {
	q := &Queue{}
	q.l = list.New()
	q.id = count
	count++
	return q
}

// Enqueue enqueues a new ReqInterface at the queue
func (q *Queue) Enqueue(el engine.ReqInterface) {
	//fmt.Printf("time: %v, queue: %v, len: %v\n", engine.GetTime(), q.id, q.Len())
	q.l.PushBack(el)
}

// Dequeue dequeues the last ReqInterface from the queue
func (q *Queue) Dequeue() engine.ReqInterface {
	el := q.l.Front()
	q.l.Remove(el)
	return el.Value.(engine.ReqInterface)
}

// Len returns the queue length
func (q *Queue) Len() int {
	return q.l.Len()
}

// PriorityQueue
type Comparable interface {
	GetCmpVal() float64
	GetServiceTime() float64
	GetInitTime() float64
}

type pQueue []Comparable

func (pq pQueue) Len() int { return len(pq) }

func (pq pQueue) Less(i, j int) bool {
	if pq[i].GetCmpVal() == pq[j].GetCmpVal() {
		// Tie-break with arrival time (FIFO for same priority)
		return pq[i].GetInitTime() < pq[j].GetInitTime()
	}
	return pq[i].GetCmpVal() < pq[j].GetCmpVal()
}

func (pq pQueue) Swap(i, j int) {
	pq[i], pq[j] = pq[j], pq[i]
}

func (pq *pQueue) Push(x interface{}) {
	item := x.(Comparable)
	*pq = append(*pq, item)
}

func (pq *pQueue) Pop() interface{} {
	old := *pq
	n := len(old)
	item := old[n-1]
	*pq = old[0 : n-1]
	return item
}

type PQueue struct {
	pq pQueue
}

func NewPQueue() *PQueue {
	q := &PQueue{}
	q.pq = make(pQueue, 0)
	heap.Init(&q.pq)

	return q
}

func (pq *PQueue) Enqueue(el engine.ReqInterface) {
	comp, ok := el.(Comparable)
	if !ok {
		panic(fmt.Sprintf("Element enqueued to PQueue does not implement blocks.Comparable interface: %T", el))
	}
	heap.Push(&pq.pq, comp)
}

func (pq *PQueue) Dequeue() engine.ReqInterface {
	return heap.Pop(&pq.pq).(engine.ReqInterface)
}

func (pq *PQueue) Len() int {
	return pq.pq.Len()
}

func (pq *PQueue) PrintQueue() {
	for _, v := range pq.pq {
		fmt.Printf("%v\t", v.GetServiceTime())
	}
}
