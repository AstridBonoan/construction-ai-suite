import React from 'react';
import {
  Box,
  Button,
  Container,
  Heading,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  Card,
  CardBody,
  VStack,
  HStack,
  Badge,
  useColorModeValue,
} from '@chakra-ui/react';

const Dashboard = () => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  return (
    <Container maxW="6xl" py={8}>
      <VStack spacing={8} align="stretch">
        <Box>
          <Heading size="lg" mb={6}>Dashboard Overview</Heading>
          <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
            <Card bg={bgColor} border="1px" borderColor={borderColor}>
              <CardBody>
                <Stat>
                  <StatLabel>Projects Monitored</StatLabel>
                  <StatNumber color="blue.600">12</StatNumber>
                </Stat>
              </CardBody>
            </Card>
            <Card bg={bgColor} border="1px" borderColor={borderColor}>
              <CardBody>
                <Stat>
                  <StatLabel>Active Risks</StatLabel>
                  <StatNumber color="red.600">3</StatNumber>
                </Stat>
              </CardBody>
            </Card>
            <Card bg={bgColor} border="1px" borderColor={borderColor}>
              <CardBody>
                <Stat>
                  <StatLabel>Critical Delays</StatLabel>
                  <StatNumber color="orange.600">1</StatNumber>
                </Stat>
              </CardBody>
            </Card>
          </SimpleGrid>
        </Box>
        <Box>
          <Heading size="md" mb={4}>Recent AI Insights</Heading>
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
            <Card bg={bgColor} border="1px" borderColor={borderColor}>
              <CardBody>
                <VStack align="start" spacing={3}>
                  <HStack>
                    <Heading size="sm">Schedule Risk</Heading>
                    <Badge colorScheme="orange">HIGH</Badge>
                  </HStack>
                  <Box fontSize="sm" color="gray.600">
                    Foundation poured behind schedule. Critical path delay detected.
                  </Box>
                  <Button size="sm" variant="ghost">View Details →</Button>
                </VStack>
              </CardBody>
            </Card>
            <Card bg={bgColor} border="1px" borderColor={borderColor}>
              <CardBody>
                <VStack align="start" spacing={3}>
                  <HStack>
                    <Heading size="sm">Resource Alert</Heading>
                    <Badge colorScheme="blue">INFO</Badge>
                  </HStack>
                  <Box fontSize="sm" color="gray.600">
                    Recommended allocation update based on team availability.
                  </Box>
                  <Button size="sm" variant="ghost">View Details →</Button>
                </VStack>
              </CardBody>
            </Card>
          </SimpleGrid>
        </Box>
      </VStack>
    </Container>
  );
};

export default Dashboard;
