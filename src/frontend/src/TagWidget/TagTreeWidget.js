import React from 'react';
import { Tree } from 'antd';

export default TagTreeWidget() {

  function refresh() {
    fetch('/api/tags/tree')
      .then(response => {
        response.json().then(data => (this.setState({ data })))
      })
  }

  const onSelect = (selectedKeys, info) => {
    console.log('selected', selectedKeys, info);
  };

  const onDoubleClick = (selectedKeys, key) => {
    this.props.addTagToSearch(key);
  }

  function dataToTree() {
    let tree = [];
    Object.keys(this.state.data).map(group => {
      let children = [];
      if (Object.keys(this.state.data[group]).length > 0) {
        Object.keys(this.state.data[group]).map(tag => {
          children.push({ title: tag, key: group + tag});
        });
        tree.push({title: group , key: group, children: children});
      } else {
        tree.push({title: group , key: group});
      }
      
    })
    return tree;
  }

  if (true) {
    const treeData = this.dataToTree();
    return (<div>
      <h1>Tag Tree</h1>
      <Tree
        treeData={treeData}
        showLine={{showLeafIcon: false}}
        showIcon={false}
        multiple
        onDoubleClick={this.onDoubleClick}
        onSelect={this.onSelect}
      />
    </div>)
  }

  return (
    <div>
      {'Loading...'}
    </div>
  );
}