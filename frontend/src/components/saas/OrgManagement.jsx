import React from 'react';
import {
  Box,
  Container,
  Heading,
  VStack,
  Card,
  CardBody,
  Text,
  HStack,
  Badge,
  Button,
  Divider,
  SimpleGrid,
  useColorModeValue,
} from '@chakra-ui/react';

const OrgManagement = () => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const users = [
    { id: 1, name: 'Alice Admin', email: 'alice@org.com', role: 'admin' },
    { id: 2, name: 'Bob Member', email: 'bob@org.com', role: 'member' },
    { id: 3, name: 'Carol Viewer', email: 'carol@org.com', role: 'viewer' },
  ];

  return (
    <Container maxW="4xl" py={8}>
      <VStack spacing={8} align="stretch">
        <Box>
          <Heading size="lg" mb={4}>Organization Settings</Heading>
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
            <Card bg={bgColor} border="1px" borderColor={borderColor}>
              <CardBody>
                <VStack align="start" spacing={2}>
                  <Heading size="sm">Organization Name</Heading>
                  <Text color="gray.600">Acme Construction Inc.</Text>
                </VStack>
              </CardBody>
            </Card>
            <Card bg={bgColor} border="1px" borderColor={borderColor}>
              <CardBody>
                <VStack align="start" spacing={2}>
                  <Heading size="sm">Current Plan</Heading>
                  <Badge colorScheme="green">Professional</Badge>
                </VStack>
              </CardBody>
            </Card>
          </SimpleGrid>
        </Box>
        <Divider />
        <Box>
          <Heading size="md" mb={4}>Team Members</Heading>
          <VStack spacing={3}>
            {users.map((user) => (
              <Card key={user.id} w="full" bg={bgColor} border="1px" borderColor={borderColor}>
                <CardBody>
                  <HStack justify="space-between" w="full">
                    <VStack align="start" spacing={0}>
                      <Text fontWeight="bold" fontSize="sm">{user.name}</Text>
                      <Text fontSize="xs" color="gray.500">{user.email}</Text>
                    </VStack>
                    <Badge colorScheme={user.role === 'admin' ? 'red' : user.role === 'member' ? 'blue' : 'gray'}>
                      {user.role.toUpperCase()}
                    </Badge>
                  </HStack>
                </CardBody>
              </Card>
            ))}
          </VStack>
          <Button mt={4} colorScheme="blue" size="sm">+ Add User</Button>
        </Box>
      </VStack>
    </Container>
  );
};

export default OrgManagement;
